# Aegis Deployment Guide

## Prerequisites

- AWS Account with Bedrock, AgentCore, Neptune, and SageMaker access
- AWS CLI configured with credentials (`aws configure`)
- Python 3.10+
- Node.js 18+
- npm or yarn

## Quick Start Deployment

### 1. Clone and Setup

```bash
git clone <repository-url>
cd agenticai_for_authorized_push_payments

# Make deployment script executable
chmod +x infrastructure/scripts/deploy.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.template .env

# Edit .env with your AWS account details
# Required: AWS_ACCOUNT_ID, AWS_REGION, KNOWLEDGE_BASE_ID (after creation)
```

### 3. Run Automated Deployment

```bash
./infrastructure/scripts/deploy.sh
```

This script will:
1. Setup Python virtual environment
2. Upload ML models to S3
3. Create DynamoDB tables
4. Setup Bedrock Knowledge Base
5. Create Bedrock Guardrails
6. Deploy agents to AgentCore Runtime
7. Build Next.js frontend
8. Provide instructions for frontend deployment

## Manual Deployment Steps

### Step 1: Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: AWS Infrastructure

#### DynamoDB Tables

```bash
python3 infrastructure/scripts/create_dynamodb_tables.py
```

Creates tables:
- `aegis-cases` - Case management
- `aegis-transactions` - Transaction history
- `aegis-customers` - Customer profiles
- `aegis-audit-logs` - Audit trail (7-year retention)
- `aegis-cases-memory` - AgentCore Memory

#### S3 Buckets

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ML Models bucket
aws s3 mb s3://aegis-ml-models-${AWS_ACCOUNT_ID}
aws s3 sync ML_DL_Models/model_output/artifacts/ s3://aegis-ml-models-${AWS_ACCOUNT_ID}/

# Knowledge Base documents bucket
aws s3 mb s3://aegis-kb-documents-${AWS_ACCOUNT_ID}
aws s3 sync knowledge_base_docs/ s3://aegis-kb-documents-${AWS_ACCOUNT_ID}/
```

### Step 3: Bedrock Knowledge Base

1. Create OpenSearch Serverless collection:

```bash
aws opensearchserverless create-collection \
  --name aegis-kb \
  --type VECTORSEARCH
```

2. Create Knowledge Base:

```bash
python3 backend/knowledge_base/setup.py
```

3. Populate with documents:

```bash
python3 backend/knowledge_base/populate.py
```

4. Copy Knowledge Base ID to `.env`:

```
KNOWLEDGE_BASE_ID=<your-kb-id>
```

### Step 4: Bedrock Guardrails

1. Navigate to AWS Bedrock Console → Guardrails
2. Create two guardrails:
   - Input Guardrails (import from `backend/guardrails/input_guardrails.json`)
   - Output Guardrails (import from `backend/guardrails/output_guardrails.json`)
3. Copy Guardrail ID to `.env`:

```
DIALOGUE_GUARDRAILS_ID=<your-guardrails-id>
```

### Step 5: Amazon Neptune (Graph Database)

1. Create Neptune cluster:

```bash
aws neptune create-db-cluster \
  --db-cluster-identifier aegis-graph \
  --engine neptune \
  --engine-version 1.3.0.0
```

2. Create Neptune instance:

```bash
aws neptune create-db-instance \
  --db-instance-identifier aegis-graph-instance \
  --db-instance-class db.r5.large \
  --engine neptune \
  --db-cluster-identifier aegis-graph
```

3. Copy endpoint to `.env`:

```
NEPTUNE_ENDPOINT=<your-neptune-endpoint>.amazonaws.com
```

### Step 6: SageMaker Endpoints (Optional)

If using SageMaker for ML models:

```bash
# Deploy fraud detector
cd backend/ml_models/sagemaker/fraud_detector
python deploy.py

# Repeat for other models
```

Or use Lambda-based inference (simpler, lower cost).

### Step 7: Deploy Agents

```bash
python3 infrastructure/scripts/deploy_agents.py
```

Agents are deployed to AWS Bedrock AgentCore Runtime with:
- Session isolation
- AgentCore Memory integration
- AgentCore Gateway for tools
- AgentCore Identity (IAM roles)
- AgentCore Observability (CloudWatch, X-Ray)

### Step 8: Frontend Deployment

#### Option A: AWS Amplify

```bash
cd frontend
npm install
amplify init
amplify add hosting
amplify publish
```

#### Option B: Vercel

```bash
cd frontend
npm install
vercel --prod
```

#### Option C: Manual to S3 + CloudFront

```bash
cd frontend
npm install
npm run build
aws s3 sync out/ s3://aegis-frontend-${AWS_ACCOUNT_ID}/
```

### Step 9: Authentication (Cognito)

1. Create Cognito User Pool:

```bash
aws cognito-idp create-user-pool \
  --pool-name aegis-analysts \
  --policies "PasswordPolicy={MinimumLength=12,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true}"
```

2. Create User Pool Client:

```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id <pool-id> \
  --client-name aegis-frontend
```

3. Create first analyst user:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <pool-id> \
  --username analyst@example.com \
  --temporary-password TempPass123! \
  --user-attributes Name=email,Value=analyst@example.com
```

## Verification

### Test Backend API

```bash
# Test transaction submission (local)
python3 -m backend.api.main
```

### Test Frontend

```bash
cd frontend
npm run dev
# Open http://localhost:3000/analyst
```

### Test Agent Invocation

```bash
python3 << EOF
from backend.agents.supervisor_agent import SupervisorAgent
import asyncio

async def test():
    agent = SupervisorAgent()
    result = await agent.investigate_transaction({
        'transaction_id': 'TEST-001',
        'customer_id': 'CUST-001',
        'amount': 5000,
        'payee_account': '12345678',
        'payee_name': 'Test Payee'
    })
    print(result)

asyncio.run(test())
EOF
```

## Monitoring

### CloudWatch Dashboards

Access pre-configured dashboards:
- Agent Performance (latency, errors)
- Fraud Detection Rate
- Model Performance
- False Positive Rate

### X-Ray Tracing

View distributed traces:

```bash
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)
```

### Logs

View agent logs:

```bash
aws logs tail /aws/lambda/aegis-supervisor-agent --follow
```

## Troubleshooting

### Issue: Knowledge Base not returning results

**Solution:**
1. Verify documents are in S3
2. Trigger re-indexing
3. Check OpenSearch cluster health

### Issue: Agents timing out

**Solution:**
1. Check CloudWatch metrics for bottlenecks
2. Increase Lambda timeout
3. Optimize parallel agent execution

### Issue: High false positive rate

**Solution:**
1. Review SHAP explanations
2. Retrain models with recent data
3. Adjust risk thresholds in `.env`

## Production Checklist

- [ ] All environment variables configured
- [ ] DynamoDB tables created with backups enabled
- [ ] Knowledge Base populated and indexed
- [ ] Guardrails created and tested
- [ ] Neptune cluster running
- [ ] ML models deployed (SageMaker or Lambda)
- [ ] Agents deployed to AgentCore Runtime
- [ ] Frontend deployed and accessible
- [ ] Cognito User Pool created
- [ ] First analyst user created
- [ ] CloudWatch alarms configured
- [ ] X-Ray tracing enabled
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented
- [ ] Security review completed
- [ ] Load testing completed

## Next Steps

1. Configure rate limiting and WAF
2. Setup CI/CD pipeline
3. Enable multi-region deployment
4. Implement A/B testing for model versions
5. Configure automated model retraining

## Support

For issues or questions:
- Check logs: CloudWatch Logs
- Review metrics: CloudWatch Dashboards
- Open issue on GitHub
- Contact: support@aegis-fraud-prevention.com



