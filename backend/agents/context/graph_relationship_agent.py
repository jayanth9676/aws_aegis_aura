"""Graph Relationship Agent - Network analysis and mule detection."""

from typing import Dict
from agents.base_agent import AegisBaseAgent
from config import AgentConfig

class GraphRelationshipAgent(AegisBaseAgent):
    """Analyzes transaction networks and detects mule accounts using graph analytics."""
    
    def __init__(self):
        config = AgentConfig.graph_relationship_config()
        super().__init__("graph_relationship_agent", config)
    
    async def execute(self, input_data: Dict) -> Dict:
        """Analyze graph relationships and detect mule patterns using AI reasoning."""
        
        entities = input_data.get('entities', {})
        session_id = input_data.get('session_id')
        sender_account = entities.get('sender_account')
        receiver_account = entities.get('receiver_account')
        
        self.logger.info(
            "Analyzing graph relationships with AI",
            sender=sender_account,
            receiver=receiver_account
        )
        
        # Query Neptune graph database
        network = await self.invoke_tool('GraphAnalysisTool', {
            'sender': sender_account,
            'receiver': receiver_account,
            'depth': 3  # 3-hop analysis
        })
        
        # Invoke GNN-based mule detection
        mule_prediction = await self.invoke_tool('MuleDetectionTool', {
            'account': receiver_account,
            'network_features': network.get('features', {})
        })
        
        # Analyze network patterns (keep rule-based detection)
        patterns = self._analyze_patterns(network, mule_prediction)
        
        # Use AI to analyze network risk
        analysis_prompt = """Analyze this transaction network for money laundering and mule account indicators:

Network Structure:
{network_summary}

GNN Mule Detection:
{mule_summary}

Detected Network Patterns:
{patterns_summary}

Based on this evidence, identify all network-related fraud risk factors. Consider:
- Mule account probability (high priority if >0.7)
- Fan-out patterns (one sender, many receivers)
- Fan-in patterns (many senders, one receiver - typical mule behavior)
- Rapid money movement through network
- Circular transaction flows (layering)
- Multiple intermediary accounts

For each risk factor:
1. Name the risk factor (e.g., "MULE_ACCOUNT_DETECTED", "FAN_OUT_PATTERN", "CIRCULAR_TRANSACTION_FLOW")
2. Assign a severity level: LOW, MEDIUM, HIGH, or CRITICAL
3. Assign a numerical weight (0-300 points, mule accounts highest)
4. Provide a brief explanation

Return your response as JSON with this structure:
{{
    "risk_factors": [
        {{
            "factor": "RISK_FACTOR_NAME",
            "severity": "CRITICAL",
            "weight": 300,
            "details": "Explanation of network risk"
        }}
    ],
    "overall_assessment": "Brief summary of network analysis",
    "confidence": 0.88
}}""".format(
            network_summary=self._summarize_network(network),
            mule_summary=self._summarize_mule_prediction(mule_prediction),
            patterns_summary=self._summarize_patterns(patterns)
        )
        
        # Get AI analysis
        ai_analysis = await self.reason_with_bedrock(
            prompt=analysis_prompt,
            context={'network': network, 'mule': mule_prediction, 'patterns': patterns}
        )
        
        # Extract risk factors from AI response
        risk_factors = ai_analysis.get('risk_factors', [])
        
        # Fallback to rule-based if AI fails
        if not risk_factors or ai_analysis.get('fallback'):
            self.logger.warning("AI analysis failed, using rule-based fallback")
            risk_factors = self._assess_risk(network, mule_prediction, patterns)
            overall_assessment = "Rule-based analysis (AI unavailable)"
            confidence = 0.5
        else:
            overall_assessment = ai_analysis.get('overall_assessment', '')
            confidence = ai_analysis.get('confidence', 0.7)
        
        result = {
            'agent': 'graph_relationship',
            'mule_risk_score': mule_prediction.get('score', 0),
            'network_patterns': patterns,
            'risk_factors': risk_factors,
            'evidence': {
                'network': network,
                'mule_prediction': mule_prediction,
                'patterns': patterns
            },
            'risk_score_contribution': mule_prediction.get('score', 0) * 100,
            'ai_assessment': overall_assessment,
            'confidence': confidence,
            'reasoning_source': 'ai' if not ai_analysis.get('fallback') else 'rules'
        }

        if session_id:
            await self.store_memory(
                f'session:{session_id}:graph_context',
                result,
                ttl=self.config.session_ttl
            )

        return result
    
    def _analyze_patterns(self, network: Dict, mule_prediction: Dict) -> Dict:
        """Analyze network patterns for suspicious behavior."""
        
        patterns = {
            'fan_out': False,
            'fan_in': False,
            'rapid_movement': False,
            'circular_flow': False,
            'layering': False
        }
        
        # Fan-out pattern (one sender, many receivers)
        if network.get('features', {}).get('out_degree', 0) > 10:
            patterns['fan_out'] = True
        
        # Fan-in pattern (many senders, one receiver)
        if network.get('features', {}).get('in_degree', 0) > 10:
            patterns['fan_in'] = True
        
        # Rapid movement (quick succession of transactions)
        if network.get('features', {}).get('avg_time_between_transactions', float('inf')) < 300:  # 5 minutes
            patterns['rapid_movement'] = True
        
        # Circular flow detection
        if network.get('features', {}).get('circular_paths', 0) > 0:
            patterns['circular_flow'] = True
        
        # Layering (multiple intermediaries)
        if network.get('features', {}).get('intermediary_count', 0) > 3:
            patterns['layering'] = True
        
        return patterns
    
    def _assess_risk(self, network: Dict, mule_prediction: Dict, patterns: Dict) -> list:
        """Assess network-related risk factors."""
        risk_factors = []
        
        # High mule probability
        mule_score = mule_prediction.get('score', 0)
        if mule_score > 0.7:
            risk_factors.append({
                'factor': 'MULE_ACCOUNT_DETECTED',
                'severity': 'CRITICAL',
                'weight': 300,
                'details': f"Mule probability: {mule_score:.2%}, Pattern: {mule_prediction.get('pattern')}"
            })
        elif mule_score > 0.5:
            risk_factors.append({
                'factor': 'POTENTIAL_MULE_ACCOUNT',
                'severity': 'HIGH',
                'weight': 200,
                'details': f"Mule probability: {mule_score:.2%}"
            })
        
        # Fan-out pattern
        if patterns['fan_out']:
            risk_factors.append({
                'factor': 'FAN_OUT_PATTERN',
                'severity': 'HIGH',
                'weight': 180,
                'details': f"Account sends to {network.get('features', {}).get('out_degree', 0)} recipients"
            })
        
        # Rapid movement
        if patterns['rapid_movement']:
            risk_factors.append({
                'factor': 'RAPID_MONEY_MOVEMENT',
                'severity': 'HIGH',
                'weight': 150,
                'details': 'Funds move through network in < 5 minutes'
            })
        
        # Circular flow
        if patterns['circular_flow']:
            risk_factors.append({
                'factor': 'CIRCULAR_TRANSACTION_FLOW',
                'severity': 'HIGH',
                'weight': 170,
                'details': 'Circular money flow detected - potential layering'
            })
        
        # Layering
        if patterns['layering']:
            risk_factors.append({
                'factor': 'TRANSACTION_LAYERING',
                'severity': 'MEDIUM',
                'weight': 120,
                'details': f"{network.get('features', {}).get('intermediary_count', 0)} intermediary accounts"
            })
        
        return risk_factors
    
    def _summarize_network(self, network: Dict) -> str:
        """Summarize network structure for AI prompt."""
        if not network or not network.get('features'):
            return "No network data available"
        
        features = network.get('features', {})
        summary = f"""
- Out-Degree (recipients): {features.get('out_degree', 0)}
- In-Degree (senders): {features.get('in_degree', 0)}
- Circular Paths: {features.get('circular_paths', 0)}
- Intermediary Accounts: {features.get('intermediary_count', 0)}
- Avg Time Between Transactions: {features.get('avg_time_between_transactions', 0)} seconds
- Total Network Nodes: {features.get('total_nodes', 0)}
- Total Network Edges: {features.get('total_edges', 0)}
"""
        return summary.strip()
    
    def _summarize_mule_prediction(self, mule_prediction: Dict) -> str:
        """Summarize GNN mule detection for AI prompt."""
        if not mule_prediction:
            return "No mule detection data available"
        
        score = mule_prediction.get('score', 0)
        pattern = mule_prediction.get('pattern', 'Unknown')
        confidence = mule_prediction.get('confidence', 0)
        
        summary = f"""
- Mule Probability: {score:.2%}
- Pattern Type: {pattern}
- Model Confidence: {confidence:.2%}
- Risk Level: {'CRITICAL' if score > 0.7 else 'HIGH' if score > 0.5 else 'MEDIUM' if score > 0.3 else 'LOW'}
"""
        return summary.strip()
    
    def _summarize_patterns(self, patterns: Dict) -> str:
        """Summarize detected patterns for AI prompt."""
        if not patterns:
            return "No patterns detected"
        
        active_patterns = [key.replace('_', ' ').title() for key, value in patterns.items() if value]
        
        if not active_patterns:
            return "No suspicious patterns detected"
        
        summary = "Active Patterns:\n"
        for pattern in active_patterns:
            summary += f"- {pattern}\n"
        
        return summary.strip()

