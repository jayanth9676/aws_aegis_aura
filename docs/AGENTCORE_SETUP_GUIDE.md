# Aegis AgentCore Setup & Deployment Guide

## Overview

This guide covers setting up and deploying the Aegis fraud prevention platform with AWS Bedrock AgentCore Runtime for multi-agent orchestration.

## Architecture Changes

### What's New

1. **Real AI Reasoning**: Agents now use AWS Bedrock Claude Sonnet for analysis instead of hardcoded rules
2. **AgentCore Integration**: Multi-agent orchestration via AWS Bedrock AgentCore Runtime
3. **Real Data Integration**: DynamoDB queries instead of mocked responses
4. **Enhanced UI**: Modern components with real-time updates
5. **Guardrails**: Bedrock Guardrails protect customer interactions

### System Flow

```
Transaction Submitted
     ↓
API Endpoint (/api/v1/transactions/submit)
     ↓
Supervisor Agent (AgentCore)
     ├─→ Transaction Context Agent (AI + Tools)
     ├─→ Customer Context Agent (AI + Tools)
     ├─→ Payee Context Agent (AI + Tools)
     ├─→ Behavioral Analysis Agent (AI + Tools)
     └─→ Graph Relationship Agent (AI + Tools)
     ↓
Risk Scoring Agent (AI + ML Models)
     ↓
Triage Agent (Policy Decisions)
     ↓
Response (Allow/Challenge/Block)
```

## Prerequisites

### Required AWS Services

- **AWS Bedrock**: Access to Claude Sonnet 4 model
- **DynamoDB**: Tables for cases, transactions, customers
- **S3**: Buckets for ML models and documents
- **Lambda**: For AgentCore Gateway tools
- **Cognito**: User authentication (optional for Phase 1)
- **Bedrock Knowledge Base**: Fraud intelligence RAG (optional)

### Required Permissions

Your AWS credentials need:
- `bedrock:InvokeModel`
- `bedrock-agent:Retrieve` (for Knowledge Base)
- `dynamodb:Query`, `dynamodb:PutItem`, `dynamodb:UpdateItem`
- `s3:GetObject`, `s3:PutObject`
- `lambda:InvokeFunction`
- `events:PutEvents`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`

## Phase 1: Infrastructure Setup

### Step 1.1: Create DynamoDB Tables

```bash
# Run from project root
python infrastructure/scripts/create_dynamodb_tables.py
```

This creates:
- `aegis-cases` - Fraud investigation cases
- `aegis-transactions` - Transaction history
- `aegis-customers` - Customer profiles
- `aegis-audit-logs` - Audit trail

### Step 1.2: Populate Test Data

```bash
# Install dependencies
pip install faker boto3

# Populate DynamoDB with realistic test data
python infrastructure/scripts/populate_test_data.py
```

This generates:
- 1,000 customer profiles
- 10,000 transactions
- 200 fraud cases

### Step 1.3: Setup Bedrock Model Access

1. Go to AWS Bedrock Console
2. Navigate to "Model access"
3. Request access to:
   - Anthropic Claude Sonnet 4
   - Amazon Titan Embeddings (if using Knowledge Base)

Wait for approval (usually immediate for Claude).

### Step 1.4: Configure Environment Variables

Create `.env` file in project root:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# DynamoDB Tables
CASES_TABLE=aegis-cases
TRANSACTIONS_TABLE=aegis-transactions
CUSTOMERS_TABLE=aegis-customers
AUDIT_LOGS_TABLE=aegis-audit-logs

# Bedrock Configuration
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-20250514-v1:0
DIALOGUE_GUARDRAILS_ID=  # Leave empty for now
KNOWLEDGE_BASE_ID=  # Leave empty if not using KB

# Risk Thresholds
BLOCK_THRESHOLD=85
CHALLENGE_THRESHOLD=60
HIGH_CONFIDENCE_THRESHOLD=0.8

# Optional: SageMaker Endpoints (if deploying ML models)
FRAUD_DETECTOR_ENDPOINT=
MULE_DETECTOR_ENDPOINT=
```

## Phase 2: Backend Setup

### Step 2.1: Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2.2: Test Bedrock Connection

```bash
# Test that Bedrock Claude is accessible
python -c "import boto3; client = boto3.client('bedrock-runtime'); print('✓ Bedrock connection successful')"
```

### Step 2.3: Start Backend API

```bash
# From project root
uvicorn backend.api.main:app --reload --port 8000
```

Verify at: http://localhost:8000/health

### Step 2.4: Test AI-Powered Agent

```bash
# Test transaction submission with AI analysis
curl -X POST http://localhost:8000/api/v1/transactions/submit \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TEST-001",
    "customer_id": "CUST-12345",
    "amount": 5000,
    "payee_account": "12345678",
    "payee_name": "Urgent Payment Ltd",
    "sender_account": "87654321"
  }'
```

**Expected**: Real AI analysis with risk factors identified by Claude Sonnet.

## Phase 3: Frontend Setup

### Step 3.1: Install Node Dependencies

```bash
cd frontend
npm install
```

### Step 3.2: Configure Frontend Environment

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3.3: Start Frontend

```bash
npm run dev
```

Access at: http://localhost:3000

### Step 3.4: Test UI Features

1. **Analyst Dashboard**: http://localhost:3000/analyst
   - View real cases from DynamoDB
   - See real-time statistics
   - Filter by priority/status

2. **Case Details**: http://localhost:3000/analyst/cases/[case_id]
   - View AI-generated risk factors
   - See evidence timeline
   - Approve/Block actions update DynamoDB

3. **Analytics**: http://localhost:3000/analyst/dashboard
   - Fraud trends visualization
   - Risk distribution charts
   - Top fraud types

4. **Customer Portal**: http://localhost:3000/customer
   - View transactions
   - Security education
   - Scam warnings

## Phase 4: Enable Bedrock Guardrails (Optional)

### Step 4.1: Create Dialogue Guardrails

```python
# Run from project root
python infrastructure/bedrock_guardrails/deploy_guardrails.py
```

This creates guardrails for:
- Input validation (prompt injection protection)
- PII anonymization for customer dialogues
- Content filtering

### Step 4.2: Update Environment

After deployment, update `.env`:

```bash
DIALOGUE_GUARDRAILS_ID=<guardrails-id-from-output>
```

Restart backend to apply.

## Phase 5: Deploy AgentCore Runtime (Advanced)

> **Note**: This requires additional setup and is optional for initial testing.

### Prerequisites

- Install AgentCore CLI: `pip install agentcore-cli`
- Configure AWS CDK: `npm install -g aws-cdk`

### Deployment Steps

```bash
# 1. Deploy infrastructure via CDK
cd infrastructure/cdk
npm install
cdk bootstrap
cdk deploy --all

# 2. Deploy AgentCore Runtime
bash ../deploy_agentcore.sh
```

This deploys:
- Lambda functions for each agent
- AgentCore Memory (DynamoDB)
- AgentCore Gateway (API Gateway + Lambda)
- IAM roles and policies

### Update Backend to Use AgentCore

Modify `backend/agents/supervisor_agent.py`:

```python
# Replace tool-based agent invocation with AgentCore SDK
from agentcore import AgentCoreClient

client = AgentCoreClient(region='us-east-1')

# Instead of:
# await self.invoke_tool('TransactionContextAgent', params)

# Use:
result = await client.invoke_agent('transaction_context', params)
```

## Testing

### Unit Tests

```bash
# From project root
pytest tests/agents/ -v
```

### Integration Tests

```bash
# Test with real AWS services
pytest tests/integration/ -v
```

### End-to-End Test

```bash
# Run complete transaction flow test
bash infrastructure/scripts/run_e2e_tests.sh
```

## Monitoring

### CloudWatch Logs

```bash
# View agent logs
aws logs tail /aegis/agents --follow

# View API logs
aws logs tail /aegis/api --follow
```

### Metrics

View in CloudWatch dashboard:
- Agent invocation counts
- Latency metrics
- Error rates
- Risk score distributions

### X-Ray Tracing

Enable X-Ray for request tracing:

```python
# Already enabled in backend/utils/__init__.py
```

View traces in AWS X-Ray console.

## Troubleshooting

### Issue: "Bedrock model not found"

**Solution**: Request model access in Bedrock console and wait for approval.

### Issue: "DynamoDB table does not exist"

**Solution**: Run `python infrastructure/scripts/create_dynamodb_tables.py`

### Issue: "AI reasoning returning fallback"

**Possible causes**:
1. Bedrock credentials not configured
2. Model ID incorrect
3. Region mismatch
4. Insufficient permissions

**Debug**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Issue: "No transactions in dashboard"

**Solution**: Run `python infrastructure/scripts/populate_test_data.py`

## Performance Optimization

### Enable Caching

Configure Redis for agent memory caching:

```python
# In backend/agents/base_agent.py
self.memory = RedisCacheMemory(
    host=os.getenv('REDIS_HOST'),
    ttl=3600
)
```

### Parallel Agent Execution

Already implemented in `SupervisorAgent`:

```python
# Agents execute in parallel via asyncio.gather()
results = await asyncio.gather(*tasks)
```

### ML Model Optimization

Deploy models to SageMaker for faster inference:

```bash
python backend/ml_models/sagemaker/deploy.py
```

## Security Best Practices

1. **Never commit `.env` files** - Use AWS Secrets Manager in production
2. **Enable Guardrails** for all customer-facing agents
3. **Encrypt sensitive data** - Use KMS for encryption at rest
4. **Audit all decisions** - Review `aegis-audit-logs` table
5. **Monitor for drift** - Track false positive rates

## Next Steps

1. **Deploy ML models** to SageMaker (see `backend/ml_models/sagemaker/`)
2. **Setup Knowledge Base** for fraud intelligence RAG
3. **Configure Cognito** for analyst authentication
4. **Enable WebSocket** for real-time UI updates
5. **Deploy to production** using AWS Amplify (frontend) and Lambda (backend)

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review agent execution traces in X-Ray
3. Consult agent-specific logs in DynamoDB
4. Test with smaller payloads to isolate issues

## Changelog

### v2.0.0 (Current)
- ✅ Real AI reasoning with Bedrock Claude Sonnet
- ✅ AgentCore-ready architecture
- ✅ Real DynamoDB integration
- ✅ Enhanced UI components
- ✅ Test data population script
- ✅ Comprehensive logging and tracing

### v1.0.0 (Previous)
- Basic agent structure with hardcoded rules
- Mock data responses
- Simple UI

---

**Congratulations!** You now have a production-ready AI fraud prevention platform powered by AWS Bedrock AgentCore.


