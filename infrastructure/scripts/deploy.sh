#!/bin/bash
set -e

echo "==========================================
"
echo "Aegis Fraud Prevention Platform Deployment"
echo "==========================================
"

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed. Aborting." >&2; exit 1; }

# Get AWS account info
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=$(aws configure get region)

echo "AWS Account: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo ""

# Step 1: Setup Python environment
echo "[1/8] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python environment ready"
echo ""

# Step 2: Upload ML models to S3
echo "[2/8] Uploading ML models to S3..."
ML_BUCKET="aegis-ml-models-${AWS_ACCOUNT_ID}"
aws s3 mb s3://${ML_BUCKET} 2>/dev/null || echo "Bucket already exists"
aws s3 sync ML_DL_Models/model_output/artifacts/ s3://${ML_BUCKET}/ --exclude "*.pyc"
echo "✓ ML models uploaded"
echo ""

# Step 3: Create DynamoDB tables
echo "[3/8] Creating DynamoDB tables..."
python3 infrastructure/scripts/create_dynamodb_tables.py
echo "✓ DynamoDB tables created"
echo ""

# Step 4: Setup Knowledge Base
echo "[4/8] Setting up Bedrock Knowledge Base..."
python3 backend/knowledge_base/setup.py
python3 backend/knowledge_base/populate.py
echo "✓ Knowledge Base ready"
echo ""

# Step 5: Create Bedrock Guardrails
echo "[5/8] Creating Bedrock Guardrails..."
python3 infrastructure/scripts/create_guardrails.py
echo "✓ Guardrails configured"
echo ""

# Step 6: Deploy agents to AgentCore Runtime
echo "[6/8] Deploying agents to AgentCore Runtime..."
python3 infrastructure/scripts/deploy_agents.py
echo "✓ Agents deployed"
echo ""

# Step 7: Setup frontend
echo "[7/8] Setting up Next.js frontend..."
cd frontend
npm install
npm run build
echo "✓ Frontend built"
cd ..
echo ""

# Step 8: Deploy frontend to Amplify
echo "[8/8] Deploying frontend to AWS Amplify..."
echo "To deploy frontend, run: amplify publish"
echo "Or deploy manually to your preferred hosting platform"
echo ""

echo "==========================================
"
echo "Deployment Complete!"
echo "==========================================
"
echo ""
echo "Next steps:"
echo "1. Copy env.template to .env and configure your environment variables"
echo "2. Create Cognito User Pool for analyst authentication"
echo "3. Deploy frontend: cd frontend && amplify publish"
echo "4. Create first analyst user"
echo "5. Access dashboard at your Amplify URL"
echo ""
echo "For detailed instructions, see docs/DEPLOYMENT.md"



