# Aegis Fraud Prevention Platform - Dataset Documentation

## Overview

This directory contains comprehensive, production-ready datasets for the **Aegis Fraud Prevention Platform**. These datasets are specifically designed to support the multi-agent fraud detection system built on AWS Bedrock AgentCore Runtime.

**Version**: 4.0  
**Generated**: 2025-10-16  
**Total Records**: 8,000+ across 10 interconnected datasets  
**System Compatibility**: AgentCore Runtime, Neptune Graph DB, DynamoDB, Redis

---

## Dataset Inventory

### Core Entity Datasets

| Dataset | Records | Description | Primary Use |
|---------|---------|-------------|-------------|
| **aegis_customers.json** | 100 | Customer master data with KYC, AML, risk profiles | Customer Context Agent, Risk Scoring |
| **aegis_accounts.json** | 295 | Bank accounts with limits and status | Account verification, Transaction validation |
| **aegis_devices.json** | 312 | Device trust data with fingerprints | Device Trust Service, Behavioral Analysis |
| **aegis_payees.json** | 11 | Payee/merchant data for CoP verification | Payee Context Agent, Watchlist Service |

### Transaction & Event Datasets

| Dataset | Records | Description | Primary Use |
|---------|---------|-------------|-------------|
| **aegis_transactions.json** | 3,208 | Transactions with ML features & fraud labels | Transaction Context Agent, ML Models |
| **aegis_behavioral_events.json** | 3,208 | Session behavioral biometrics | Behavioral Analysis Agent |
| **aegis_fraud_alerts.json** | 344 | Fraud alerts with SHAP explanations | Supervisor Agent, Triage Agent |

### Investigation & Operations

| Dataset | Records | Description | Primary Use |
|---------|---------|-------------|-------------|
| **aegis_call_history.json** | 326 | Customer contact records with analysts | Dialogue Agent, Investigation Agent |
| **aegis_cases.json** | 267 | Case management with AI copilot data | Investigation Agent, Analyst UI |
| **aegis_graph_relationships.json** | 500 | Entity relationships for network analysis | Graph Relationship Agent, Neptune |

---

## Data Characteristics

### Fraud Distribution
- **Total Transactions**: 3,208
- **Fraudulent**: 209 (6.51%)
- **Legitimate**: 2,999 (93.49%)
- **Fraud Types**: APP Scams, Investment Scams, Romance Scams, Crypto Scams, Invoice Fraud, Account Takeover, Mule Accounts

### Customer Segmentation
- **Premium**: 25% (high net worth, low risk)
- **Standard**: 60% (typical customers)
- **Vulnerable**: 15% (elderly, low digital literacy, high risk)

### Alert Prioritization
- **Critical**: 20% (immediate escalation required)
- **High**: 50% (analyst review within 24h)
- **Medium**: 20% (routine investigation)
- **Low**: 10% (automated monitoring)

---

## Schema Documentation

### 1. Customer Dataset (`aegis_customers.json`)

**Purpose**: Comprehensive customer profiles for risk assessment and fraud detection

**Key Sections**:
- **personal_information**: KYC data, identity verification, sanctions checks
- **contact_information**: Multi-channel contact details with verification status
- **employment**: Income verification and employment status
- **customer_details**: Segment, tenure, credit score, product holdings
- **compliance**: AML risk level, CDD status, regulatory reporting
- **behavioral_profile**: Digital literacy, banking adoption, device familiarity
- **vulnerability_assessment**: Scam susceptibility scoring and education status
- **risk_profile**: Overall risk scoring with protective/risk factors

**Sample Structure**:
```json
{
  "customer_id": "AEGIS-CUST-000001",
  "personal_information": {
    "name_full": "Oliver James Thompson",
    "date_of_birth": "1989-05-17",
    "age": 36,
    "kyc_status": "Verified",
    "pep_status": false,
    "sanctions_check": "Clear"
  },
  "risk_profile": {
    "overall_risk_score": 15,
    "risk_category": "Low",
    "fraud_flag": false
  }
}
```

**Agent Usage**:
- Customer Context Agent: Complete customer profile retrieval
- Risk Scoring Agent: Risk factor analysis
- Dialogue Agent: Customer communication preferences

---

### 2. Accounts Dataset (`aegis_accounts.json`)

**Purpose**: Bank account information with transaction limits and status

**Key Fields**:
- `account_id`: Unique account identifier (AEGIS-ACC-######)
- `customer_id`: Link to customer record
- `account_number`, `sort_code`: Banking identifiers
- `account_type`: Current, Savings, Credit Card, Business, Premium
- `balance`: Current account balance
- `daily_limit`, `monthly_limit`: Transaction limits
- `is_mule_account`: Mule account flag (2% rate)

**Agent Usage**:
- Transaction Context Agent: Account validation
- Triage Agent: Limit breach detection
- PayeeContext Agent: Account verification

---

### 3. Transactions Dataset (`aegis_transactions.json`)

**Purpose**: Transaction data with ML features and fraud labels for model training

**Key Features**:
- **Basic**: amount, currency, type, date, time, payee
- **Device**: device_id, device_model, device_fingerprint, known_device
- **Location**: ip_address, ip_country, location_risk
- **Risk Scoring**: risk_score, location_risk, amount_risk, velocity_risk
- **ML**: ml_fraud_probability, is_fraud, fraud_type
- **Compliance**: ctr_flag, sar_flag

**Fraud Patterns**:
- Unusual hours (fraud concentrated in 00:00-06:00, 22:00-24:00)
- Unknown devices (70% of fraud from unknown devices)
- High-risk countries (SG, MT, LV, CY over-represented in fraud)
- Large amounts (fraudulent transactions average 10x legitimate)

**Agent Usage**:
- Transaction Context Agent: Transaction analysis
- ML Model Service: Feature extraction, fraud prediction
- Risk Scoring Agent: Ensemble model scoring

---

### 4. Behavioral Events Dataset (`aegis_behavioral_events.json`)

**Purpose**: Session-level behavioral biometrics for fraud detection

**Key Metrics**:
- **Session**: session_id, session_duration_seconds, event_timestamp
- **Interaction**: page_views, mouse_movements, keyboard_events
- **Anomaly**: anomaly_score, typing_pattern_anomaly
- **Flags**: hesitation_detected, copy_paste_detected, new_payee_flag
- **Failures**: authentication_failures, device_change_detected

**Behavioral Indicators**:
- **Hesitation**: Pauses before confirming high-risk actions
- **Copy-Paste**: Pasting account numbers (potential scam)
- **Speed**: Unusually fast navigation (account takeover)
- **Authentication**: Multiple failed attempts

**Agent Usage**:
- Behavioral Analysis Agent: Session risk scoring
- Dialogue Agent: Hesitation-based intervention timing

---

### 5. Fraud Alerts Dataset (`aegis_fraud_alerts.json`)

**Purpose**: Fraud alerts with rule-based detection and ML confidence

**Alert Strategies**:
- `RUL-TX901`: Large Fund Transfer Post Password Change
- `RUL-TX230`: Business Invoice Redirection
- `RUL-TX817`: New Device + Account Cleanout
- `RUL-TX155`: Drip Transfer Anomaly
- `RUL-TX488`: Investment Scam First-Time Pattern
- `RUL-TX778`: Full Balance Outflow Detection
- `RUL-CRY101`: Cryptocurrency Rapid Conversion
- `RUL-RS001`: Romance Scam Pattern

**Escalation Levels**:
- **L1**: Risk score 600-750 (routine analyst review)
- **L2**: Risk score 750-900 (senior analyst, same-day)
- **L3**: Risk score 900+ (critical, immediate escalation)

**SHAP Explanations**:
Each alert includes SHAP (SHapley Additive exPlanations) values for model interpretability:
```json
{
  "shap_explanation": {
    "top_features": [
      {"feature": "transaction_amount", "contribution": 0.32},
      {"feature": "device_risk", "contribution": 0.25},
      {"feature": "location_anomaly", "contribution": 0.18}
    ]
  }
}
```

**Agent Usage**:
- Supervisor Agent: Alert orchestration and routing
- Triage Agent: Policy-based decisioning
- Investigation Agent: Case creation and evidence gathering

---

### 6. Devices Dataset (`aegis_devices.json`)

**Purpose**: Device trust scoring and fingerprinting

**Key Fields**:
- `device_fingerprint`: Unique device identifier (16-char hex)
- `device_type`: Mobile, Desktop, Tablet
- `device_model`, `device_os`, `browser`: Device characteristics
- `is_trusted`: Trust flag (85% of devices trusted)
- `trust_score`: 0.0-1.0 trust score
- `biometric_enabled`: Biometric authentication capability
- `location_history`: Historical locations

**Trust Scoring Factors**:
- First seen date (older = more trusted)
- Consistent location patterns
- Biometric enrollment
- No suspicious activity history

**Agent Usage**:
- Behavioral Analysis Agent: Device risk scoring
- Transaction Context Agent: Device validation

---

### 7. Payees Dataset (`aegis_payees.json`)

**Purpose**: Payee/merchant verification and watchlist checking

**Key Fields**:
- `payee_type`: Individual, Business, Cryptocurrency Exchange, Investment Platform, Merchant
- `watchlist_status`: Clear (90%), Flagged (8%), Blocked (2%)
- `cop_verified`: Confirmation of Payee verification status
- `sanctions_check`: Sanctions screening result
- `fraud_reports_count`: Historical fraud report count
- `risk_score`: 0-100 payee risk score

**Watchlist Integration**:
- Sanctions lists (OFAC, EU, UN)
- Known fraud entities
- Cryptocurrency scam addresses
- Investment fraud platforms

**Agent Usage**:
- Payee Context Agent: Payee verification
- CoP Verification Tool: Confirmation of Payee API
- Watchlist Service: Sanctions and fraud checking

---

### 8. Call History Dataset (`aegis_call_history.json`)

**Purpose**: Customer contact records with analyst performance data

**Key Fields**:
- `analyst_id`, `analyst_name`, `analyst_team`, `analyst_level`
- `call_type`: Inbound (30%), Outbound (70%)
- `call_outcome_category`: Customer reached, No Response, Voicemail, Disconnected
- `call_duration_seconds`: Actual call duration
- `call_quality_score`: 0.75-0.98 quality rating
- `customer_satisfaction_score`: 3.0-5.0 rating
- `resolution_time_hours`: Time to case resolution

**Analyst Teams**:
- Fraud Ops East/West
- Device Trust Unit
- Transaction Risk
- Customer Protection
- Investment Risk
- Behavioral Risk
- Commercial Fraud
- Crypto Risk

**Agent Usage**:
- Dialogue Agent: Call script generation
- Investigation Agent: Contact attempt tracking
- Reporting: Analyst performance analytics

---

### 9. Cases Dataset (`aegis_cases.json`)

**Purpose**: Case management for Investigation Agent workflows

**Case Lifecycle**:
1. **Open**: Newly created from alert
2. **In Progress**: Analyst actively investigating
3. **Pending Customer**: Awaiting customer response
4. **Pending Review**: Investigation complete, awaiting approval
5. **Resolved - Fraud Confirmed**: Fraud confirmed, actions taken
6. **Resolved - False Positive**: Legitimate transaction
7. **Closed**: Case finalized

**AI Copilot Recommendations**:
Each case includes AI-generated recommendations:
```json
{
  "ai_copilot_recommendations": [
    {
      "recommendation_type": "Similar Cases",
      "confidence": 0.87,
      "details": "Found 8 similar patterns in historical data"
    },
    {
      "recommendation_type": "Risk Assessment",
      "confidence": 0.92,
      "details": "ML model fraud probability: 0.89"
    }
  ]
}
```

**Evidence Collection**:
- Transaction logs
- Device fingerprints
- IP geolocation
- Customer call recordings
- Behavioral biometrics
- Email communications
- Payee verification results
- Similar pattern analysis

**Agent Usage**:
- Investigation Agent: Case management, evidence synthesis
- AI Copilot: Recommendation generation
- Reporting: Case metrics and outcomes

---

### 10. Graph Relationships Dataset (`aegis_graph_relationships.json`)

**Purpose**: Entity relationships for Neptune graph database

**Relationship Types**:
- `TRANSACTS_WITH`: Customer-to-customer money flows
- `SHARES_DEVICE`: Multiple customers using same device
- `SHARES_IP`: Same IP address usage
- `SAME_PAYEE`: Common payee relationships
- `SIMILAR_PATTERN`: Behavioral pattern similarity
- `MONEY_FLOW`: Financial connection tracking
- `LINKED_ACCOUNT`: Account linkage indicators
- `FAMILY_MEMBER`: Known family relationships

**Key Fields**:
- `relationship_strength`: 0.1-1.0 confidence score
- `transaction_count`: Number of shared transactions
- `total_amount`: Total amount transacted
- `risk_indicator`: Boolean flag for suspicious relationships
- `shared_attributes`: IP Address, Device Fingerprint, Payee, Timing Pattern

**Agent Usage**:
- Graph Relationship Agent: Network analysis
- Pattern Detection: Mule account ring detection
- Risk Scoring: Network-based risk amplification

---

## Integration with Aegis Agents

### Agent-to-Dataset Mapping

| Agent | Primary Datasets | Secondary Datasets |
|-------|-----------------|-------------------|
| **Supervisor Agent** | fraud_alerts | transactions, customers, cases |
| **Customer Context Agent** | customers | accounts, devices, behavioral_events |
| **Transaction Context Agent** | transactions | accounts, payees, behavioral_events |
| **Payee Context Agent** | payees | transactions |
| **Behavioral Analysis Agent** | behavioral_events | devices, transactions |
| **Graph Relationship Agent** | graph_relationships | customers, transactions |
| **Risk Scoring Agent** | transactions, fraud_alerts | All datasets |
| **Triage Agent** | fraud_alerts | customers, transactions |
| **Dialogue Agent** | call_history, customers | fraud_alerts, cases |
| **Investigation Agent** | cases | All datasets |

---

## Data Generation

### Generator Script

The datasets are generated using `generate_aegis_datasets.py`:

```bash
cd datasets/aegis_datasets
python generate_aegis_datasets.py
```

**Configuration** (in script):
```python
TOTAL_CUSTOMERS = 100
TRANSACTIONS_PER_CUSTOMER_RANGE = (15, 50)
FRAUD_RATE = 0.08  # 8% fraud rate
VULNERABLE_CUSTOMER_RATE = 0.15  # 15% vulnerable
```

### Reproducibility

- **Random Seed**: 42 (for consistent generation)
- **Deterministic**: Same configuration produces identical output
- **Scalable**: Adjust `TOTAL_CUSTOMERS` for larger datasets

---

## Usage Guidelines

### 1. DynamoDB Integration

Load customers into DynamoDB:
```python
import boto3
import json

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aegis-customers')

with open('aegis_customers.json', 'r') as f:
    data = json.load(f)
    for customer in data['customers']:
        table.put_item(Item=customer)
```

### 2. Neptune Graph Loading

Load relationships into Neptune:
```python
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

graph = Graph()
g = graph.traversal().withRemote(DriverRemoteConnection('wss://your-neptune-endpoint:8182/gremlin', 'g'))

with open('aegis_graph_relationships.json', 'r') as f:
    data = json.load(f)
    for rel in data['relationships']:
        g.V().has('id', rel['source_entity_id']).addE(rel['relationship_type']).to(
            g.V().has('id', rel['target_entity_id'])
        ).property('strength', rel['relationship_strength']).next()
```

### 3. ML Model Training

Prepare features for ML:
```python
import pandas as pd
import json

with open('aegis_transactions.json', 'r') as f:
    data = json.load(f)
    df = pd.DataFrame(data['transactions'])

# Feature engineering
features = ['amount', 'risk_score', 'location_risk', 'amount_risk', 'velocity_risk']
X = df[features]
y = df['is_fraud']

# SHAP values available in fraud_alerts dataset
```

---

## Data Quality & Validation

### Quality Metrics

- **Completeness**: 100% (all required fields populated)
- **Consistency**: Referential integrity maintained
- **Accuracy**: Realistic distributions based on industry data
- **Timeliness**: Recent timestamps (last 90 days)

### Validation Checks

Run validation script:
```bash
python validate_aegis_datasets.py
```

Checks performed:
- ✓ Foreign key integrity (customer_id, transaction_id, alert_id)
- ✓ Date consistency (no future dates)
- ✓ Amount ranges (positive, realistic)
- ✓ Enum values (valid categories only)
- ✓ Fraud rate within acceptable range (5-10%)

---

## Compliance & Security

### Data Classification

- **Level**: Confidential
- **PII**: Contains customer personal information
- **Encryption**: Encrypt at rest and in transit
- **Access Control**: Role-based access (analysts, developers)

### Regulatory Compliance

- **KYC**: Know Your Customer data maintained
- **AML**: Anti-Money Laundering risk levels
- **CDD**: Customer Due Diligence status
- **GDPR**: Data retention and privacy compliance
- **PSR**: Payment Services Regulations adherence

### Retention Policy

- **Transactional Data**: 7 years
- **Audit Trails**: 7 years
- **Customer Data**: Duration of relationship + 7 years
- **Case Records**: 10 years (regulatory requirement)

---

## Extending the Datasets

### Adding New Customers

```python
from generate_aegis_datasets import AegisDataGenerator

generator = AegisDataGenerator()
new_customer = generator.generate_customer(101)
# Add to customers.json
```

### Creating Custom Scenarios

Modify fraud patterns in `generate_aegis_datasets.py`:

```python
# Add new fraud type
fraud_type = "Crypto Investment Scam"

# Generate specific transaction
transaction = generator.generate_transaction(
    customer_id="AEGIS-CUST-000001",
    account_id="AEGIS-ACC-000001",
    idx=1,
    is_fraud=True,
    fraud_type=fraud_type
)
```

---

## Support & Maintenance

### Reporting Issues

For dataset issues or enhancements:
1. Check validation output
2. Review generator configuration
3. Submit issue with reproducible example

### Version History

- **v4.0** (2025-10-16): Production-ready datasets with full agent integration
- **v3.0** (2024-12-19): Enhanced schema from authorized_scams_dataset
- **v2.0** (2024-01-15): Initial structured datasets
- **v1.0** (2023): Prototype datasets

---

## References

- [Aegis Architecture Documentation](../../docs/ARCHITECTURE.md)
- [Agent Development Guide](../../docs/AGENTS.md)
- [ML Model Documentation](../../ML_DL_Models/README.md)
- [Responsible AI Guidelines](../../docs/RESPONSIBLE_AI.md)

---

**Last Updated**: 2025-10-16  
**Maintained By**: Aegis Data Platform Team  
**License**: Proprietary - Internal Use Only

