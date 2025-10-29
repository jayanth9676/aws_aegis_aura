# APP Fraud Detection Guide: Comprehensive Indicators and Response

## Document Metadata
- **Document Type**: Fraud Typology Guide
- **Category**: APP Scam Detection
- **Keywords**: APP fraud, authorized push payment, social engineering, impersonation, romance scams, investment scams
- **Target Audience**: Fraud analysts, risk managers, customer service agents
- **Last Updated**: 2025-10-19
- **Version**: 2.0

## Executive Summary
This comprehensive guide provides detailed indicators, detection methods, and response procedures for Authorized Push Payment (APP) fraud. APP fraud is a sophisticated social engineering attack where victims are manipulated into willingly authorizing payments to criminal accounts.

## Key APP Fraud Indicators (High Priority)

### 🚨 Critical Red Flags (Immediate Action Required)
1. **Active Call During Transaction**
   - Customer on phone while making payment
   - Evidence of coaching or pressure
   - Unusual hesitation or confusion
   - **Risk Score Impact**: +40 points

2. **New Payee + High Amount**
   - First-time payment to recipient
   - Amount >£1,000 or >50% of account balance
   - Round numbers (£1000, £5000, £10000)
   - **Risk Score Impact**: +30 points

3. **Confirmation of Payee (CoP) Mismatch**
   - Name doesn't match account holder
   - Partial name matches
   - **Risk Score Impact**: +35 points

### ⚠️ High-Risk Indicators
1. **Urgency and Pressure Tactics**
   - "Act now or lose money/account"
   - "Don't hang up the phone"
   - "Don't tell anyone about this"
   - **Risk Score Impact**: +25 points

2. **Unusual Transaction Patterns**
   - Transactions outside normal hours
   - Multiple rapid transactions
   - Full balance transfers
   - **Risk Score Impact**: +20 points

3. **Device and Location Anomalies**
   - New device login
   - Unusual geographic location
   - VPN or proxy usage
   - **Risk Score Impact**: +15 points

## Detailed Fraud Typologies

### 1. Bank Impersonation Scams
**How it works**: Fraudster poses as bank's fraud department
**Common scenarios**:
- "Your account has been compromised"
- "We need to move your money to a safe account"
- "This is urgent - act now"

**Detection indicators**:
- Customer mentions "bank called me"
- Claims of account compromise
- Pressure to act immediately
- Requests for remote access

**Example conversation patterns**:
- "The bank said my account was hacked"
- "They told me to transfer money to protect it"
- "I'm on the phone with them now"

### 2. Police/Government Impersonation
**How it works**: Fraudster poses as police or government official
**Common scenarios**:
- "You're under investigation"
- "We need to verify your identity"
- "Your money needs to be moved for safety"

**Detection indicators**:
- Customer mentions police/government contact
- Claims of investigation or arrest
- Requests for money to "clear name"
- Threats of legal action

### 3. Romance Scams
**How it works**: Long-term relationship building for financial gain
**Common scenarios**:
- Online relationship with requests for money
- Claims of emergencies requiring funds
- Promises of future repayment

**Detection indicators**:
- Large transfers to individuals
- International payments
- Emotional distress during transaction
- Vague explanations for payment purpose

### 4. Investment Scams
**How it works**: Fake investment opportunities with high returns
**Common scenarios**:
- Cryptocurrency investments
- Forex trading opportunities
- Property investment schemes

**Detection indicators**:
- Payments to investment platforms
- Claims of guaranteed returns
- Pressure to invest quickly
- Unlicensed investment companies

## Behavioral Analysis Patterns

### Typing Behavior Indicators
1. **Hesitation Patterns**
   - Unusual pauses between keystrokes
   - Multiple backspaces and corrections
   - Slow typing speed changes
   - **Confidence Level**: High

2. **Copy-Paste Behavior**
   - Account details copied from external source
   - Sudden typing speed changes
   - Unusual character sequences
   - **Confidence Level**: High

3. **Session Anomalies**
   - Unusually long session duration
   - Multiple browser tabs open
   - Frequent page navigation
   - **Confidence Level**: Medium

### Communication Patterns
1. **Voice Stress Indicators**
   - Changes in tone, pitch, or speed
   - Background noise or coaching
   - Hesitation in responses
   - **Confidence Level**: High

2. **Language Patterns**
   - Scripted or rehearsed responses
   - Inconsistent story details
   - Use of specific terminology
   - **Confidence Level**: Medium

## Response Procedures

### Immediate Actions (0-5 minutes)
1. **Block Transaction**
   - Hold payment immediately
   - Document all evidence
   - Notify fraud team

2. **Customer Contact**
   - Call on verified number (NOT number used during transaction)
   - Use standard verification questions
   - Assess customer awareness

### Investigation Process (5-30 minutes)
1. **Evidence Collection**
   - Document all indicators
   - Record customer statements
   - Collect transaction details

2. **Risk Assessment**
   - Calculate composite risk score
   - Determine fraud probability
   - Plan response strategy

### Resolution (30+ minutes)
1. **If Fraud Confirmed**
   - Keep transaction blocked
   - Provide customer support
   - File SAR within 24 hours
   - Attempt fund recovery

2. **If Legitimate**
   - Apologize for delay
   - Release transaction
   - Update customer profile
   - Document for future reference

## Risk Scoring Matrix

| Indicator | Weight | Score Range | Action Threshold |
|-----------|--------|-------------|------------------|
| Active Call | 40% | 0-40 | >20 = High Risk |
| CoP Mismatch | 35% | 0-35 | >15 = High Risk |
| New Payee + High Amount | 30% | 0-30 | >15 = High Risk |
| Urgency Pressure | 25% | 0-25 | >10 = Medium Risk |
| Device Anomalies | 15% | 0-15 | >8 = Medium Risk |

**Total Risk Score**: 0-145 points
- **0-30**: Low Risk (Allow with monitoring)
- **31-60**: Medium Risk (Hold and investigate)
- **61-100**: High Risk (Block and contact customer)
- **101+**: Critical Risk (Block immediately, urgent contact)

## Common False Positives

### Legitimate Scenarios
1. **Genuine Emergencies**
   - Medical emergencies
   - Family crises
   - Business emergencies

2. **New Relationships**
   - Legitimate new business partners
   - Family members in need
   - Charitable donations

3. **Investment Activities**
   - Licensed investment platforms
   - Established financial advisors
   - Regulated investment products

### Mitigation Strategies
1. **Enhanced Verification**
   - Additional identity checks
   - Independent verification
   - Third-party confirmation

2. **Customer Education**
   - Scam awareness training
   - Warning systems
   - Educational materials

## Regulatory Compliance

### UK PSR Requirements
- Mandatory reimbursement for APP fraud victims
- Maximum claim: £415,000
- 5-day reimbursement timeframe
- Shared liability between banks

### AUSTRAC Requirements
- SAR filing within 24 hours
- Customer due diligence
- Transaction monitoring
- Record keeping (7 years)

## Technology Integration

### AI/ML Detection
- Behavioral biometrics
- Device fingerprinting
- Network analysis
- Pattern recognition

### Real-time Monitoring
- Transaction screening
- Velocity analysis
- Geographic monitoring
- Device tracking

## Training and Awareness

### Staff Training
- Fraud recognition
- Customer communication
- Investigation procedures
- Regulatory compliance

### Customer Education
- Scam awareness
- Warning systems
- Reporting channels
- Prevention tips

## Performance Metrics

### Detection Accuracy
- True Positive Rate: >95%
- False Positive Rate: <3%
- Response Time: <5 minutes
- Customer Satisfaction: >90%

### Key Performance Indicators
- Fraud Prevention Rate
- False Positive Rate
- Investigation Time
- Customer Contact Success Rate
- SAR Filing Compliance

## Continuous Improvement

### Regular Updates
- Monthly fraud pattern analysis
- Quarterly procedure reviews
- Annual training updates
- Technology enhancements

### Feedback Loops
- Customer feedback
- Staff input
- Regulatory guidance
- Industry best practices

---

**Document Classification**: CONFIDENTIAL - FRAUD PREVENTION
**Review Cycle**: Quarterly
**Next Review Date**: 2026-01-19
**Approved By**: Head of Fraud Prevention
