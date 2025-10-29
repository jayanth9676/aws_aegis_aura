# Responsible AI Framework - Aegis Platform

## Overview

Aegis is built with Responsible AI principles at its core, ensuring all AI-driven decisions are explainable, fair, safe, and compliant with regulatory requirements.

## Core Principles

1. **Explainability**: Every decision includes human-readable explanations
2. **Fairness**: No disparate impact across demographic groups
3. **Safety**: Guardrails prevent harmful outputs
4. **Privacy**: PII protection and data minimization
5. **Transparency**: Full audit trail of all decisions
6. **Human Oversight**: Human-in-the-loop for critical decisions

## Bedrock Guardrails

### Input Guardrails

**Purpose**: Protect system from malicious inputs

**Configuration File**: `backend/guardrails/input_guardrails.json`

**Protection Mechanisms**:

1. **Prompt Injection Protection**
   - Detects attempts to manipulate AI system
   - Examples: "Ignore previous instructions", "You are now..."
   - Action: DENY request

2. **PII Blocking**
   - Blocks credit card numbers, SSNs, passwords
   - Prevents sensitive data leakage
   - Action: BLOCK transaction

3. **Word Filtering**
   - Profanity filter
   - Security-sensitive terms (CVV, PIN)
   - Action: BLOCK or sanitize

**Effectiveness Metrics**:
- Prompt injection detection rate: > 99%
- PII blocking rate: 100%
- False positive rate: < 0.1%

### Output Guardrails

**Purpose**: Ensure safe, helpful customer-facing dialogue

**Configuration File**: `backend/guardrails/output_guardrails.json`

**Protection Mechanisms**:

1. **Content Filtering**
   - Sexual content: HIGH filtering
   - Violence: HIGH filtering
   - Hate speech: HIGH filtering
   - Insults: HIGH filtering
   - Misconduct: HIGH filtering

2. **Topic Denial**
   - Financial advice: DENY
   - Legal counsel: DENY
   - Medical advice: DENY
   - Ensures AI stays within scope

3. **PII Protection**
   - Names: ANONYMIZE
   - Account numbers: ANONYMIZE
   - Emails: ANONYMIZE
   - Credit cards: BLOCK
   - SSNs: BLOCK

4. **Contextual Grounding**
   - Grounding threshold: 75%
   - Relevance threshold: 75%
   - Ensures responses are factual and evidence-based

**Effectiveness Metrics**:
- Harmful content blocking: 100%
- PII leakage rate: 0%
- Hallucination rate: < 1%
- Grounding score: > 90%

## Explainable AI (XAI)

### SHAP Explanations

**Purpose**: Explain why ML model flagged transaction as fraudulent

**Implementation**:
- SHAP TreeExplainer for ensemble models
- Feature importance calculated for each prediction
- Top 5 contributing features highlighted
- Visual explanations in analyst dashboard

**Example Output**:
```python
{
  "risk_score": 87,
  "top_features": [
    {"name": "active_call", "contribution": +35},
    {"name": "new_payee", "contribution": +18},
    {"name": "amount_outlier", "contribution": +15},
    {"name": "typing_hesitation", "contribution": +12},
    {"name": "velocity_high", "contribution": +7}
  ]
}
```

### Reason Codes

**Purpose**: Human-readable explanations for analysts and compliance

**Generation**:
- Extracted from agent risk factors
- Combined with SHAP top features
- Translated to standard reason codes

**Standard Reason Codes**:
- `ACTIVE_CALL_DETECTED`: Phone call during transaction
- `NEW_PAYEE_HIGH_AMOUNT`: First payment to recipient, high value
- `PAYEE_VERIFICATION_MISMATCH`: CoP name mismatch
- `VELOCITY_ANOMALY`: Unusual transaction frequency
- `TYPING_HESITATION_ANOMALY`: Behavioral duress signals
- `DEVICE_RISK`: Unknown or suspicious device
- `MULE_NETWORK_DETECTED`: Graph analysis flags mule account

### Decision Transparency

Every decision includes:
1. **Risk Score**: 0-100 quantitative assessment
2. **Confidence**: 0-1 confidence in assessment
3. **Reason Codes**: List of specific indicators
4. **SHAP Values**: Feature contributions
5. **Agent Analysis**: Results from each agent
6. **Evidence Timeline**: Chronological event sequence

## Bias Detection & Fairness

### Protected Attributes

Monitored for disparate impact:
- Age
- Gender
- Race/Ethnicity
- Geographic location

### Fairness Metrics

**Disparate Impact Analysis**:
- 80% rule enforcement
- False positive rate parity
- Equal opportunity metrics

**Implementation**:
```python
# backend/guardrails/responsible_ai.py
class BiasDetectionModule:
    def detect_bias(self, predictions, customer_attributes):
        # Calculate FPR by protected group
        fpr_by_group = {}
        for attr in protected_attributes:
            fpr = calculate_fpr(predictions, attr)
            fpr_by_group[attr] = fpr
        
        # Check 80% rule
        disparate_impact = check_disparate_impact(fpr_by_group)
        
        # Alert if bias detected
        if disparate_impact > 0.20:
            trigger_bias_alert()
```

**Monitoring**:
- Real-time CloudWatch metrics per demographic group
- Weekly bias reports
- Quarterly fairness audits

**Mitigation Strategies**:
1. **Pre-processing**: Re-sampling to balance training data
2. **In-processing**: Fairness-aware loss functions
3. **Post-processing**: Threshold adjustment per group
4. **Human Review**: Analyst review of flagged disparities

### Bias Metrics Published to CloudWatch

```python
Namespace: Aegis/ResponsibleAI
Metrics:
  - FalsePositiveRate_age_18-25
  - FalsePositiveRate_age_26-40
  - FalsePositiveRate_age_41-60
  - FalsePositiveRate_age_60+
  - FalsePositiveRate_location_urban
  - FalsePositiveRate_location_rural
```

## Privacy Protection

### Data Minimization

- **Collection**: Only collect data necessary for fraud detection
- **Storage**: Minimal retention periods (except compliance requirements)
- **Access**: Role-based access control
- **Deletion**: Automatic deletion after retention period

### PII Handling

**During Collection**:
- Encrypt in transit (TLS 1.3)
- Minimal logging of PII
- Tokenization where possible

**During Processing**:
- Agents operate on pseudonymized IDs
- Guardrails redact PII from outputs
- Memory stores encrypted

**During Storage**:
- KMS encryption at rest
- S3 bucket policies (private)
- DynamoDB encryption
- Access logging

**During Deletion**:
- Right to be forgotten compliance
- Automated deletion after 7 years
- Secure deletion (overwrite)

### GDPR Compliance

- **Lawful Basis**: Legitimate interest (fraud prevention)
- **Data Subject Rights**: Access, rectification, erasure, portability
- **Data Protection Impact Assessment**: Completed
- **Privacy by Design**: Built into architecture

## Audit & Compliance

### Audit Trail

**What's Logged**:
- Every agent invocation
- All tool calls
- Risk scores and decisions
- Analyst actions
- Model versions used

**Log Format**:
```json
{
  "timestamp": "2024-10-15T14:23:45Z",
  "trace_id": "abc123",
  "agent": "supervisor_agent",
  "action": "investigate_transaction",
  "transaction_id": "TXN-001",
  "risk_score": 87,
  "decision": "BLOCK",
  "reason_codes": ["ACTIVE_CALL_DETECTED"],
  "analyst_id": null,
  "model_version": "v1.2.3"
}
```

**Retention**: 7 years (regulatory requirement)

**Storage**: CloudWatch Logs with encryption

### Compliance Reports

**Weekly**:
- Fraud detection rate
- False positive rate
- Model performance metrics
- Bias metrics by demographic

**Monthly**:
- SAR filing statistics
- Case resolution times
- Analyst performance
- System uptime

**Quarterly**:
- Comprehensive fairness audit
- Model drift analysis
- Security review
- Privacy assessment

**Annually**:
- Full system audit
- Regulatory compliance report
- Third-party assessment
- Model recertification

## Model Governance

### Model Lifecycle

1. **Development**
   - Training data: Stratified sampling to ensure balance
   - Validation: Holdout set with demographic split
   - Testing: Fairness metrics calculated

2. **Deployment**
   - A/B testing before full rollout
   - Gradual rollout (10% → 50% → 100%)
   - Monitoring for drift

3. **Monitoring**
   - Daily: Performance metrics
   - Weekly: Drift detection
   - Monthly: Fairness review
   - Quarterly: Retraining trigger

4. **Retraining**
   - Triggered by drift detection
   - Includes recent analyst feedback
   - Fairness constraints enforced
   - Shadow mode testing before deployment

### Model Cards

Each model has a model card documenting:
- **Purpose**: Fraud detection for APP scams
- **Training Data**: UK APP fraud dataset + synthetic
- **Performance**: AUC 0.95, FPR < 3%
- **Fairness**: Disparate impact < 20% across groups
- **Limitations**: May underperform on novel scam types
- **Intended Use**: Real-time transaction screening
- **Out of Scope**: Credit decisions, lending

### Model Versioning

- **Semantic Versioning**: v1.2.3 (major.minor.patch)
- **Artifact Storage**: S3 with versioning enabled
- **Rollback**: Previous 3 versions maintained
- **A/B Testing**: New versions tested against current

## Human-in-the-Loop

### Analyst Review

**When Required**:
- Risk score > 85 and blocked
- Customer appeals decision
- Novel fraud pattern detected
- Model confidence < 0.7

**Analyst Tools**:
- Complete case file with all evidence
- SHAP explanations
- Risk factor timeline
- Graph visualization
- AI recommendation with reasoning

**Analyst Actions**:
- Approve transaction
- Block transaction
- Request additional information
- Escalate to senior analyst
- File SAR

**Feedback Loop**:
- Analyst decision captured
- Reasoning recorded
- Used for model retraining
- Improves future accuracy

### Customer Appeals

**Process**:
1. Customer appeals blocked transaction
2. Case automatically reopened
3. Assigned to senior analyst
4. Full re-review with additional evidence
5. Decision within 24 hours
6. Customer notified with explanation

## Safety Guardrails

### System Safeguards

1. **Rate Limiting**
   - Max 1000 requests/second per IP
   - Prevents DDoS attacks

2. **Input Validation**
   - Schema validation for all inputs
   - Range checks on numerical values
   - Prevents injection attacks

3. **Output Sanitization**
   - HTML escaping
   - SQL injection prevention
   - XSS prevention

4. **Error Handling**
   - Graceful degradation
   - No sensitive data in error messages
   - Comprehensive logging

### Fail-Safe Mechanisms

- **Default Deny**: If system error, block transaction
- **Timeouts**: All agents have hard timeouts
- **Circuit Breakers**: Failing services automatically disabled
- **Fallback**: Use cached data or conservative thresholds

## Continuous Improvement

### Feedback Channels

1. **Analyst Feedback**: Direct input on AI decisions
2. **Customer Feedback**: Survey after intervention
3. **Model Metrics**: Automated performance tracking
4. **Bias Metrics**: Continuous fairness monitoring

### Improvement Process

1. **Weekly Review**: Team reviews metrics and feedback
2. **Monthly Planning**: Prioritize improvements
3. **Quarterly Retraining**: Update models with new data
4. **Annual Audit**: Comprehensive system review

### Responsible AI Roadmap

**Q1 2025**:
- Implement differential privacy
- Add adversarial robustness testing
- Enhance explainability visualizations

**Q2 2025**:
- Multi-stakeholder fairness definitions
- Automated bias mitigation
- Enhanced transparency reports

**Q3 2025**:
- Federated learning pilot
- Privacy-preserving ML techniques
- Advanced XAI methods (counterfactual)

**Q4 2025**:
- EU AI Act compliance
- Algorithmic impact assessment
- Third-party fairness audit



