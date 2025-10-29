# APP Fraud Investigation Standard Operating Procedure

## Purpose
This SOP defines the standard procedure for investigating suspected Authorized Push Payment (APP) fraud cases escalated by the Aegis AI system.

## Scope
Applies to all fraud analysts handling APP scam investigations.

## Procedure

### 1. Case Receipt and Initial Review (< 2 minutes)

**Inputs:**
- Aegis case ID
- Risk score and confidence level
- AI-generated summary
- Transaction details
- Context agent analysis

**Actions:**
1. Review AI risk score and confidence
2. Read AI-generated summary of key risk factors
3. Verify case priority (HIGH/MEDIUM/LOW)
4. Acknowledge case receipt in system

### 2. Evidence Review (< 5 minutes)

**Review all available evidence:**

**Transaction Context:**
- Transaction amount and payee details
- Historical transaction patterns
- Velocity analysis results
- Confirmation of Payee (CoP) results

**Behavioral Signals:**
- Active call indicator (CRITICAL)
- Typing hesitation patterns
- Device fingerprint analysis
- Session anomalies

**Customer Profile:**
- Age and vulnerability scores
- Previous fraud victim status
- Account tenure
- Typical transaction behavior

**Network Analysis:**
- Mule account indicators
- Payment network patterns
- Receiving account risk

**SHAP Explainability:**
- Top contributing risk factors
- Feature importance visualization
- Model confidence scores

### 3. Decision Matrix

| Risk Score | Active Call | CoP Mismatch | Action |
|------------|-------------|--------------|--------|
| >90 | Yes | Any | BLOCK + Urgent Contact |
| >85 | Any | Yes | BLOCK + Contact |
| 70-85 | Yes | Any | HOLD + Contact |
| 60-85 | No | Yes | HOLD + Request Verification |
| <60 | No | No | ALLOW with monitoring |

### 4. Customer Contact Protocol

**For BLOCKED transactions:**
1. Call customer on verified phone number (NOT number used during transaction)
2. Identify yourself and institution
3. Explain suspicious transaction detected
4. Verify customer awareness of transaction
5. Ask open-ended questions about transaction purpose
6. Listen for signs of coaching or duress

**Red flags during call:**
- Customer sounds confused or uncertain
- Another person coaching in background
- Story doesn't match transaction details
- Pressure to approve transaction quickly

**Questions to ask:**
- "Can you explain the purpose of this payment?"
- "How do you know the person/company you're paying?"
- "Have you verified their details independently?"
- "Are you currently on another call or with someone?"
- "Did someone contact you asking for this payment?"

### 5. Determine Legitimacy

**Indicators of legitimate transaction:**
- Customer confidently explains purpose
- Known relationship with payee
- Can provide independent verification
- No coaching detected
- Details match CoP verification

**Indicators of scam:**
- Customer uncertain or evasive
- Claims of emergency/urgency
- Cannot verify payee independently
- Signs of coaching
- Story changes during conversation
- Matches known scam typology

### 6. Take Action

**If FRAUD CONFIRMED:**
1. Keep transaction blocked
2. Explain to customer they're likely scam victim
3. Provide emotional support (non-judgmental)
4. Document full details of scam
5. File SAR within 24 hours
6. Report to Action Fraud
7. Attempt fund recovery with receiving bank
8. Provide customer with scam victim resources

**If LEGITIMATE:**
1. Apologize for delay
2. Explain security procedures
3. Release transaction
4. Document reasoning
5. Add to customer profile for future reference

**If UNCERTAIN:**
1. Keep transaction on hold
2. Request additional verification from customer
3. Escalate to senior analyst
4. Set review deadline (max 4 hours)

### 7. Documentation Requirements

**All cases must include:**
- Analyst ID and timestamp
- Summary of investigation
- Customer contact notes (verbatim quotes where relevant)
- Decision and reasoning
- Any additional evidence gathered
- Follow-up actions required

### 8. SAR Filing (if fraud confirmed)

**Required within 24 hours:**
1. Complete SAR template in system
2. Include all evidence from Aegis
3. Add analyst observations
4. Attach supporting documentation
5. Submit through approved channel
6. Notify compliance team

### 9. Feedback to AI System

**After case resolution:**
- Confirm/correct AI risk assessment
- Identify any missed indicators
- Flag false positives for model retraining
- Document lessons learned

## Quality Standards

- **Response time**: Acknowledge escalation <5 minutes
- **Investigation time**: Complete review <30 minutes for HIGH priority
- **Documentation**: Complete within 1 hour of case closure
- **SAR filing**: Within 24 hours of fraud confirmation

## Escalation

Escalate to senior analyst if:
- Risk score >95 with uncertain legitimacy
- Customer threatens legal action
- Transaction value >£100,000
- Complex multi-party transaction
- Regulatory concern identified



