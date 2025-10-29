# Aegis Agent Specifications

## Overview

Aegis implements 13 specialized AI agents, each optimized for a specific function in the fraud investigation workflow. All agents are built on the Strands framework and deployed to AWS Bedrock AgentCore Runtime.

## Agent Catalog

### 1. Supervisor Agent

**Role**: Central Orchestrator

**Purpose**: Manages the end-to-end fraud investigation workflow

**Key Responsibilities**:
- Receive transaction for analysis
- Invoke Context Agents in parallel
- Aggregate results from all agents
- Route to Analysis Agents
- Invoke Triage Agent for final decision
- Store investigation summary in AgentCore Memory

**Configuration**:
- Model: Claude 4 Sonnet
- Temperature: 0.5 (balanced)
- Timeout: 60s
- Max Retries: 3

**Inputs**:
```python
{
  "transaction_id": str,
  "customer_id": str,
  "amount": float,
  "payee_account": str,
  "payee_name": str,
  "device_fingerprint": str,
  "session_data": dict
}
```

**Outputs**:
```python
{
  "action": "ALLOW|CHALLENGE|BLOCK",
  "risk_score": float,
  "confidence": float,
  "reason_codes": list[str],
  "decision_details": dict
}
```

**Performance SLA**: < 500ms end-to-end

---

### 2. Transaction Context Agent

**Role**: Context Gathering

**Purpose**: Analyze transaction history and velocity patterns

**Key Responsibilities**:
- Retrieve 90-day transaction history
- Calculate velocity scores
- Detect new payees
- Verification of Payee (CoP) check
- Identify transaction anomalies

**Tools Used**:
- TransactionAnalysisTool
- VelocityAnalysisTool
- VerificationOfPayeeTool

**Risk Factors Detected**:
- NEW_PAYEE_HIGH_AMOUNT
- VELOCITY_ANOMALY
- PAYEE_VERIFICATION_MISMATCH
- ROUND_AMOUNT

**Performance SLA**: < 15ms

---

### 3. Customer Context Agent

**Role**: Context Gathering

**Purpose**: Build 360-degree customer profile

**Key Responsibilities**:
- Retrieve KYC data
- Calculate vulnerability scores
- Analyze customer lifecycle
- Check fraud history
- Assess risk profile

**Tools Used**:
- CustomerAnalysisTool
- KYCDataTool

**Vulnerability Indicators**:
- Age > 70 or < 25
- Previous fraud victim
- Low digital literacy
- Recent life events

**Performance SLA**: < 15ms

---

### 4. Payee Context Agent

**Role**: Context Gathering

**Purpose**: Verify and assess payee risk

**Key Responsibilities**:
- Confirmation of Payee verification
- Watchlist screening
- Sanctions list checking
- Merchant risk assessment

**Tools Used**:
- VerificationOfPayeeTool
- WatchlistTool
- SanctionsScreeningTool

**Risk Indicators**:
- CoP mismatch
- Watchlist hit
- High-risk jurisdiction
- New merchant account

**Performance SLA**: < 10ms

---

### 5. Behavioral Analysis Agent

**Role**: Context Gathering

**Purpose**: Detect duress and behavioral anomalies

**Key Responsibilities**:
- Analyze typing patterns
- Detect hesitation indicators
- Device fingerprinting
- Session anomaly detection
- **Active call detection** (CRITICAL)

**Tools Used**:
- BehavioralAnalysisTool (ML model)
- DeviceIntelligenceTool

**Critical Signals**:
- ACTIVE_CALL_DETECTED (phone call during transaction)
- TYPING_HESITATION_ANOMALY
- COPY_PASTE_DETECTED
- MULTIPLE_AUTH_FAILURES
- DEVICE_RISK

**Performance SLA**: < 20ms

---

### 6. Graph Relationship Agent

**Role**: Context Gathering

**Purpose**: Network analysis and mule detection

**Key Responsibilities**:
- Query Neptune graph database
- Detect mule networks
- Money flow pattern analysis
- Relationship mapping

**Tools Used**:
- GraphAnalysisTool (Neptune queries)
- MuleDetectionTool (GNN model)

**Analysis Outputs**:
- Mule probability score
- Network centrality metrics
- Money flow patterns
- Connected entities

**Performance SLA**: < 25ms

---

### 7. Risk Scoring Agent

**Role**: Analysis

**Purpose**: Synthesize context and generate final risk score

**Key Responsibilities**:
- Extract features from all context agents
- Invoke ML fraud detection ensemble
- Generate SHAP explanations
- Calculate weighted ensemble risk score
- Determine confidence level
- Generate human-readable reason codes

**Tools Used**:
- FraudDetectionTool (ML ensemble)
- SHAPExplainerTool

**Ensemble Weights**:
- ML Model: 40%
- Transaction Context: 25%
- Behavioral Context: 25%
- Graph Analysis: 10%

**Outputs**:
```python
{
  "risk_score": float (0-100),
  "confidence": float (0-1),
  "top_risk_factors": list,
  "shap_values": list,
  "reason_codes": list[str],
  "ml_score": float
}
```

**Performance SLA**: < 25ms

---

### 8. Intel Agent

**Role**: Analysis

**Purpose**: Retrieve contextual intelligence from Knowledge Base

**Key Responsibilities**:
- RAG queries against Bedrock Knowledge Base
- Retrieve fraud typologies
- Find relevant SOPs
- Extract regulatory guidance
- Match transaction pattern to known scams

**Tools Used**:
- KnowledgeBaseTool (Bedrock KB)

**Knowledge Base Contents**:
- 50+ fraud typology documents
- 20+ Standard Operating Procedures
- Regulatory requirements
- Case studies

**Performance SLA**: < 100ms

---

### 9. Triage Agent

**Role**: Decision

**Purpose**: Policy-driven decision making

**Key Responsibilities**:
- Evaluate risk score against thresholds
- Determine action (ALLOW/CHALLENGE/BLOCK)
- Execute payment controls
- Escalate high-risk cases
- Route to appropriate next agent

**Decision Matrix**:
| Risk Score | Confidence | Action |
|------------|-----------|---------|
| ≥ 85 | ≥ 0.8 | BLOCK + Escalate |
| 60-84 | Any | CHALLENGE |
| < 60 | Any | ALLOW |

**Tools Used**:
- PaymentAPITool (hold/block/allow)
- EscalationTool (create case)

**Performance SLA**: < 10ms

---

### 10. Dialogue Agent

**Role**: Decision/Action

**Purpose**: Customer-facing conversational intervention

**Key Responsibilities**:
- Generate contextual warnings
- Ask verification questions
- Educate about scam tactics
- **Protected by Bedrock Guardrails**

**Guardrails Applied**:
- Input: Prompt injection protection, PII blocking
- Output: Content filtering, PII redaction, topic denial, grounding

**Conversation Strategy**:
- Supportive, non-alarming tone
- Specific, evidence-based questions
- Educational content
- Clear action options (cancel/proceed)

**Configuration**:
- Model: Claude 4 Sonnet
- Temperature: 0.8 (creative)
- Guardrails: Output Guardrails ID
- Max Tokens: 500

**Performance SLA**: < 20ms

---

### 11. Investigation Agent

**Role**: Decision/Action

**Purpose**: Deep-dive analysis for escalated cases

**Key Responsibilities**:
- Comprehensive evidence gathering
- Timeline construction
- Pattern matching across cases
- Analyst support and recommendations

**Tools Used**:
- ForensicAnalysisTool
- EvidenceCollectionTool
- CaseManagementTool

**Configuration**:
- Extended timeout: 120s (complex investigations)
- Max Tokens: 8192 (detailed analysis)

**Performance SLA**: < 2 minutes

---

### 12. Policy Decision Agent

**Role**: Decision/Action

**Purpose**: Human-in-the-loop decision support

**Key Responsibilities**:
- Present evidence to analyst
- Explain AI reasoning
- Capture analyst feedback
- Record final decision
- Feed back to training pipeline

**Tools Used**:
- CaseManagementTool
- AnalystFeedbackTool

**Feedback Loop**:
- Analyst confirms/overrides AI decision
- Reasoning captured
- Used for model retraining
- Bias detection analysis

**Performance SLA**: Real-time (analyst-paced)

---

### 13. Regulatory Reporting Agent

**Role**: Decision/Action

**Purpose**: Automated SAR/STR generation

**Key Responsibilities**:
- Generate SAR narratives
- Pull templates from Knowledge Base
- Populate with case evidence
- Format for regulatory submission
- Track filing status

**Tools Used**:
- KnowledgeBaseTool (SAR templates)
- SARGenerationTool
- RegulatoryAPITool

**Compliance**:
- UK: Suspicious Activity Report (SAR)
- US: FinCEN SAR
- EU: Suspicious Transaction Report (STR)

**Performance SLA**: < 30s

---

## Agent Communication Protocol

### Message Format

```python
{
  "agent_id": str,
  "timestamp": str,
  "trace_id": str,
  "input_data": dict,
  "output_data": dict,
  "metadata": {
    "latency_ms": float,
    "model_version": str,
    "confidence": float
  }
}
```

### Session Management

- **Session ID**: `session:{transaction_id}`
- **Memory Keys**: `session:{id}:transaction`, `session:{id}:context`, etc.
- **TTL**: 3600s (1 hour)
- **Cleanup**: Automatic via DynamoDB TTL

### Error Handling

- **Graceful Degradation**: Continue with partial results
- **Retries**: Up to 3 attempts with exponential backoff
- **Fallback**: Use cached data or default values
- **Logging**: All errors logged to CloudWatch

## Performance Metrics

### Per-Agent SLAs

| Agent | Target Latency | Max Timeout |
|-------|---------------|-------------|
| Supervisor | 500ms (total) | 60s |
| Transaction Context | 15ms | 30s |
| Customer Context | 15ms | 30s |
| Payee Context | 10ms | 30s |
| Behavioral | 20ms | 30s |
| Graph Relationship | 25ms | 30s |
| Risk Scoring | 25ms | 30s |
| Intel (RAG) | 100ms | 30s |
| Triage | 10ms | 10s |
| Dialogue | 20ms | 20s |
| Investigation | 2min | 10min |
| Policy Decision | Real-time | N/A |
| Regulatory | 30s | 5min |

### Success Metrics

- **Availability**: 99.9%
- **Error Rate**: < 1%
- **Timeout Rate**: < 0.1%
- **Accuracy**: AUC > 0.95
- **False Positive Rate**: < 3%

## Monitoring

Each agent publishes metrics to CloudWatch:
- Invocation count
- Latency (p50, p95, p99)
- Error count
- Success rate
- Tool invocation metrics

Dashboard: `Aegis-Agent-Performance`



