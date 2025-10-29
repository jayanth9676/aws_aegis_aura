"""Regulatory Reporting Agent - Automated SAR/STR generation and filing."""

from typing import Dict
from datetime import datetime
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class RegulatoryReportingAgent(AegisBaseAgent):
    """Generates Suspicious Activity Reports (SAR) and handles regulatory filing."""
    
    def __init__(self, name: str = "regulatory_reporting_agent", config: AgentConfig = None):
        if config is None:
            config = AgentConfig.regulatory_reporting_config()
        super().__init__(name, config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Generate SAR/STR and prepare for regulatory filing."""
        
        case_id = input_data.get('case_id')
        analyst_decision = input_data.get('analyst_decision')
        session_id = input_data.get('session_id')
        
        self.logger.info(
            "Generating regulatory report",
            case_id=case_id
        )
        
        # Only generate SAR if fraud confirmed
        if analyst_decision not in ['BLOCK', 'FRAUD_CONFIRMED']:
            return {
                'sar_generated': False,
                'reason': 'No fraud confirmed - SAR not required'
            }
        
        # Retrieve full case data
        if input_data.get('transaction') and input_data.get('context_results'):
            case_data = input_data
        else:
            case_data = await self.invoke_tool('CaseManagementTool', {
                'action': 'get',
                'case_id': case_id
            })
        
        # Retrieve SAR template from Knowledge Base
        sar_template = await self.query_knowledge_base(
            "SAR suspicious activity report template UK requirements",
            top_k=1
        )
        
        # Generate SAR narrative
        sar_narrative = await self._generate_sar_narrative(case_data, sar_template)
        
        # Prepare SAR document
        sar_document = {
            'sar_id': f"SAR-{case_id}",
            'case_id': case_id,
            'report_date': datetime.utcnow().isoformat(),
            'institution': 'Aegis Bank',  # Would be configured
            'narrative': sar_narrative,
            'subject': {
                'customer_id': case_data.get('transaction', {}).get('customer_id'),
                'account_number': case_data.get('transaction', {}).get('sender_account')
            },
            'suspicious_activity': {
                'date': case_data.get('transaction', {}).get('timestamp'),
                'amount': case_data.get('transaction', {}).get('amount'),
                'type': 'Authorized Push Payment Fraud',
                'risk_score': case_data.get('risk_score')
            },
            'reason_codes': case_data.get('reason_codes', []),
            'analyst_id': input_data.get('analyst_id'),
            'status': 'DRAFT'
        }
        
        # Store SAR
        await self.invoke_tool('SARStorageTool', {
            'sar_document': sar_document
        })
        
        result = {
            'sar_generated': True,
            'sar_id': sar_document['sar_id'],
            'status': 'DRAFT',
            'requires_review': True,
            'filing_deadline': self._calculate_filing_deadline()
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:regulatory_report',
                result,
                ttl=self.config.long_term_storage and self.config.session_ttl or None
            )

        return result
    
    async def _generate_sar_narrative(self, case_data: Dict, template: list) -> str:
        """Generate SAR narrative using AI with structured reasoning."""
        
        transaction = case_data.get('transaction', {})
        evidence = case_data.get('evidence', {})
        
        sar_prompt = """Generate a comprehensive Suspicious Activity Report (SAR) for this fraud case:

Transaction Details:
{transaction_summary}

Risk Assessment:
- AI Risk Score: {risk_score}/100
- Confidence: {confidence:.0%}
- Pattern Type: {pattern_type}

Key Risk Indicators:
{risk_indicators}

Evidence Summary:
{evidence_summary}

Investigation Findings:
{investigation_findings}

Generate a structured SAR that meets UK regulatory requirements:

Return your response as JSON with this structure:
{{
    "narrative": "Professional 200-300 word narrative describing the suspicious activity, specific red flags, and why it warrants reporting",
    "key_facts": [
        "Critical fact 1",
        "Critical fact 2",
        "Critical fact 3"
    ],
    "regulatory_basis": "Legal basis for SAR filing (e.g., POCA 2002, MLR 2017)",
    "recommended_actions": [
        "Action 1 for compliance team",
        "Action 2 for compliance team"
    ],
    "urgency_level": "ROUTINE" | "PRIORITY" | "URGENT",
    "confidence": 0.90
}}""".format(
            transaction_summary=self._summarize_transaction(transaction),
            risk_score=case_data.get('risk_score', 0),
            confidence=case_data.get('confidence', 0),
            pattern_type=case_data.get('pattern_type', 'Unknown'),
            risk_indicators=self._format_reason_codes(case_data.get('reason_codes', [])),
            evidence_summary=self._format_evidence(evidence),
            investigation_findings=self._format_investigation_findings(case_data)
        )
        
        ai_sar = await self.reason_with_bedrock(
            prompt=sar_prompt,
            context={'case': case_data, 'transaction': transaction}
        )
        
        # If AI generation succeeds, return structured narrative
        if not ai_sar.get('fallback') and ai_sar.get('narrative'):
            narrative_parts = [
                ai_sar.get('narrative', ''),
                "\n\nKEY FACTS:",
                *[f"• {fact}" for fact in ai_sar.get('key_facts', [])],
                f"\n\nREGULATORY BASIS: {ai_sar.get('regulatory_basis', 'POCA 2002, MLR 2017')}",
                "\n\nRECOMMENDED ACTIONS:",
                *[f"• {action}" for action in ai_sar.get('recommended_actions', [])]
            ]
            return "\n".join(narrative_parts)
        else:
            # Fallback to template-based narrative
            self.logger.warning("AI SAR generation failed, using template fallback")
            return self._generate_template_sar(transaction, case_data)
    
    def _summarize_transaction(self, transaction: Dict) -> str:
        """Summarize transaction for SAR."""
        return f"""
- Date/Time: {transaction.get('timestamp', 'Unknown')}
- Amount: £{transaction.get('amount', 0):,.2f}
- From Account: {transaction.get('sender_account', 'Unknown')}
- To Account: {transaction.get('payee_account', 'Unknown')}
- Payee Name: {transaction.get('payee_name', 'Unknown')}
- Customer ID: {transaction.get('customer_id', 'Unknown')}
"""
    
    def _format_investigation_findings(self, case_data: Dict) -> str:
        """Format investigation findings for SAR."""
        findings = []
        
        # AI assessments from context agents
        context_results = case_data.get('context_results', {})
        for agent_name, result in context_results.items():
            if isinstance(result, dict) and result.get('ai_assessment'):
                findings.append(f"• {agent_name}: {result.get('ai_assessment')[:100]}...")
        
        if not findings:
            findings.append("• Automated fraud detection analysis completed")
        
        return "\n".join(findings)
    
    def _generate_template_sar(self, transaction: Dict, case_data: Dict) -> str:
        """Generate template-based SAR as fallback."""
        amount = transaction.get('amount', 0)
        payee = transaction.get('payee_name', 'Unknown')
        risk_score = case_data.get('risk_score', 0)
        
        return f"""SUSPICIOUS ACTIVITY REPORT

On {transaction.get('timestamp', 'DATE')}, this institution detected suspicious payment activity involving customer account {transaction.get('sender_account', 'ACCOUNT')}.

TRANSACTION DETAILS:
A payment of £{amount:,.2f} was initiated to {payee} (Account: {transaction.get('payee_account', 'UNKNOWN')}). Our AI-powered fraud detection system assigned a risk score of {risk_score}/100 to this transaction.

SUSPICIOUS INDICATORS:
{self._format_reason_codes(case_data.get('reason_codes', []))}

ANALYSIS:
This activity exhibits characteristics consistent with Authorized Push Payment (APP) fraud. The combination of risk factors and behavioral indicators warrant regulatory reporting under the Proceeds of Crime Act 2002 and Money Laundering Regulations 2017.

RECOMMENDED ACTION:
Compliance review required. Customer contact may be necessary pending investigation outcome.

Generated by Aegis Fraud Prevention System"""
    
    def _format_reason_codes(self, reason_codes: list) -> str:
        """Format reason codes for narrative."""
        if not reason_codes:
            return "- No specific reason codes"
        
        return "\n".join(f"- {code}" for code in reason_codes)
    
    def _format_evidence(self, evidence: Dict) -> str:
        """Format evidence summary."""
        summary = []
        
        if evidence.get('behavioral_analysis'):
            behavioral = evidence['behavioral_analysis']
            if behavioral.get('duress_detected'):
                summary.append("- Behavioral indicators of duress detected")
        
        if evidence.get('transaction_context'):
            tx_context = evidence['transaction_context']
            if tx_context.get('new_payee'):
                summary.append("- Payment to new recipient")
        
        return "\n".join(summary) if summary else "- Standard transaction evidence"
    
    def _calculate_filing_deadline(self) -> str:
        """Calculate SAR filing deadline (typically 30 days in UK)."""
        from datetime import timedelta
        deadline = datetime.utcnow() + timedelta(days=30)
        return deadline.isoformat()

