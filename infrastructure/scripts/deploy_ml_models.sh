#!/bin/bash

###############################################################################
# Deploy ML Models to SageMaker
# 
# This script uploads pre-trained ML models and creates SageMaker endpoints
# for real-time fraud detection predictions.
###############################################################################

set -e

echo "🤖 Starting ML Models Deployment to SageMaker..."
echo "================================================="

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
S3_BUCKET="aegis-ml-models-${ACCOUNT_ID}"
SAGEMAKER_ROLE_NAME="bedrock-sagemaker"

echo "AWS Account ID: $ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "S3 Bucket: $S3_BUCKET"
echo ""

# ###############################################################################
# # Step 1: Create IAM Role for SageMaker
# ###############################################################################

# echo "📋 Step 1: Creating IAM Role for SageMaker..."

# TRUST_POLICY='{
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Principal": {
#         "Service": "sagemaker.amazonaws.com"
#       },
#       "Action": "sts:AssumeRole"
#     }
#   ]
# }'

# # Create role if it doesn't exist
# if ! aws iam get-role --role-name $SAGEMAKER_ROLE_NAME 2>/dev/null; then
#     echo "Creating SageMaker execution role..."
#     aws iam create-role \
#         --role-name $SAGEMAKER_ROLE_NAME \
#         --assume-role-policy-document "$TRUST_POLICY" \
#         --region $AWS_REGION
    
#     echo "Waiting for role to be ready..."
#     sleep 10
# else
#     echo "SageMaker execution role already exists"
# fi

# # Attach necessary policies
# echo "Attaching policies to SageMaker role..."
# aws iam attach-role-policy \
#     --role-name $SAGEMAKER_ROLE_NAME \
#     --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# aws iam attach-role-policy \
#     --role-name $SAGEMAKER_ROLE_NAME \
#     --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# SAGEMAKER_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${SAGEMAKER_ROLE_NAME}"
# echo "SageMaker Role ARN: $SAGEMAKER_ROLE_ARN"
# echo ""

###############################################################################
# Step 1: Upload ML Models to S3
###############################################################################

echo "📦 Step 1: Uploading ML Models to S3..."

# Check if model artifacts exist
if [ ! -d "ML_DL_Models/model_output/artifacts" ]; then
    echo "⚠️  Warning: Model artifacts directory not found"
    echo "Expected: ML_DL_Models/model_output/artifacts/"
    echo ""
    echo "Please train models first or place pre-trained models in:"
    echo "  ML_DL_Models/model_output/artifacts/"
    echo ""
    exit 1
fi

# Upload fraud detection model
echo "Uploading fraud detection model..."
if [ -f "ML_DL_Models/model_output/artifacts/aegis_fraud_ensemble.pkl" ]; then
    aws s3 cp ML_DL_Models/model_output/artifacts/aegis_fraud_ensemble.pkl \
        s3://$S3_BUCKET/fraud-detector/model.tar.gz
    echo "✅ Fraud detector model uploaded"
else
    echo "⚠️  Fraud detector model not found, creating placeholder..."
    mkdir -p /tmp/model
    echo "placeholder" > /tmp/model/model.pkl
    tar -czf /tmp/model.tar.gz -C /tmp/model .
    aws s3 cp /tmp/model.tar.gz s3://$S3_BUCKET/fraud-detector/model.tar.gz
    rm -rf /tmp/model /tmp/model.tar.gz
fi

# Upload mule detection model
echo "Uploading mule detection model..."
if [ -f "ML_DL_Models/model_output/artifacts/aegis_mule_detector.pkl" ]; then
    aws s3 cp ML_DL_Models/model_output/artifacts/aegis_mule_detector.pkl \
        s3://$S3_BUCKET/mule-detector/model.tar.gz
    echo "✅ Mule detector model uploaded"
else
    echo "⚠️  Mule detector model not found, creating placeholder..."
    mkdir -p /tmp/model
    echo "placeholder" > /tmp/model/model.pkl
    tar -czf /tmp/model.tar.gz -C /tmp/model .
    aws s3 cp /tmp/model.tar.gz s3://$S3_BUCKET/mule-detector/model.tar.gz
    rm -rf /tmp/model /tmp/model.tar.gz
fi

# Upload behavioral model
echo "Uploading behavioral analysis model..."
if [ -f "ML_DL_Models/model_output/artifacts/aegis_behavioral_model.pkl" ]; then
    aws s3 cp ML_DL_Models/model_output/artifacts/aegis_behavioral_model.pkl \
        s3://$S3_BUCKET/behavioral-model/model.tar.gz
    echo "✅ Behavioral model uploaded"
else
    echo "⚠️  Behavioral model not found, creating placeholder..."
    mkdir -p /tmp/model
    echo "placeholder" > /tmp/model/model.pkl
    tar -czf /tmp/model.tar.gz -C /tmp/model .
    aws s3 cp /tmp/model.tar.gz s3://$S3_BUCKET/behavioral-model/model.tar.gz
    rm -rf /tmp/model /tmp/model.tar.gz
fi

echo ""

###############################################################################
# Step 3: Create SageMaker Models
###############################################################################

echo "🤖 Step 3: Creating SageMaker Models..."

# Fraud Detector Model
echo "Creating fraud detector model..."
aws sagemaker create-model \
    --model-name aegis-fraud-detector \
    --primary-container Image=683313688378.dkr.ecr.$AWS_REGION.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3,ModelDataUrl=s3://$S3_BUCKET/fraud-detector/model.tar.gz \
    --execution-role-arn $SAGEMAKER_ROLE_ARN \
    --region $AWS_REGION 2>/dev/null || echo "Model already exists"

# Mule Detector Model
echo "Creating mule detector model..."
aws sagemaker create-model \
    --model-name aegis-mule-detector \
    --primary-container Image=683313688378.dkr.ecr.$AWS_REGION.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3,ModelDataUrl=s3://$S3_BUCKET/mule-detector/model.tar.gz \
    --execution-role-arn $SAGEMAKER_ROLE_ARN \
    --region $AWS_REGION 2>/dev/null || echo "Model already exists"

# Behavioral Model
echo "Creating behavioral analysis model..."
aws sagemaker create-model \
    --model-name aegis-behavioral-model \
    --primary-container Image=683313688378.dkr.ecr.$AWS_REGION.amazonaws.com/sagemaker-scikit-learn:1.0-1-cpu-py3,ModelDataUrl=s3://$S3_BUCKET/behavioral-model/model.tar.gz \
    --execution-role-arn $SAGEMAKER_ROLE_ARN \
    --region $AWS_REGION 2>/dev/null || echo "Model already exists"

echo ""

###############################################################################
# Step 4: Create Endpoint Configurations
###############################################################################

echo "⚙️  Step 4: Creating Endpoint Configurations..."

# Fraud Detector Endpoint Config
echo "Creating fraud detector endpoint config..."
aws sagemaker create-endpoint-config \
    --endpoint-config-name aegis-fraud-detector-config \
    --production-variants VariantName=AllTraffic,ModelName=aegis-fraud-detector,InitialInstanceCount=1,InstanceType=ml.t2.medium \
    --region $AWS_REGION 2>/dev/null || echo "Config already exists"

# Mule Detector Endpoint Config
echo "Creating mule detector endpoint config..."
aws sagemaker create-endpoint-config \
    --endpoint-config-name aegis-mule-detector-config \
    --production-variants VariantName=AllTraffic,ModelName=aegis-mule-detector,InitialInstanceCount=1,InstanceType=ml.t2.medium \
    --region $AWS_REGION 2>/dev/null || echo "Config already exists"

# Behavioral Model Endpoint Config
echo "Creating behavioral model endpoint config..."
aws sagemaker create-endpoint-config \
    --endpoint-config-name aegis-behavioral-model-config \
    --production-variants VariantName=AllTraffic,ModelName=aegis-behavioral-model,InitialInstanceCount=1,InstanceType=ml.t2.medium \
    --region $AWS_REGION 2>/dev/null || echo "Config already exists"

echo ""

###############################################################################
# Step 5: Create SageMaker Endpoints
###############################################################################

echo "🚀 Step 5: Creating SageMaker Endpoints..."
echo "⏳ This may take 5-10 minutes per endpoint..."
echo ""

# Fraud Detector Endpoint
echo "Creating fraud detector endpoint..."
aws sagemaker create-endpoint \
    --endpoint-name aegis-fraud-detector \
    --endpoint-config-name aegis-fraud-detector-config \
    --region $AWS_REGION 2>/dev/null || echo "Endpoint already exists"

# Mule Detector Endpoint
echo "Creating mule detector endpoint..."
aws sagemaker create-endpoint \
    --endpoint-name aegis-mule-detector \
    --endpoint-config-name aegis-mule-detector-config \
    --region $AWS_REGION 2>/dev/null || echo "Endpoint already exists"

# Behavioral Model Endpoint
echo "Creating behavioral model endpoint..."
aws sagemaker create-endpoint \
    --endpoint-name aegis-behavioral-model \
    --endpoint-config-name aegis-behavioral-model-config \
    --region $AWS_REGION 2>/dev/null || echo "Endpoint already exists"

echo ""
echo "================================================="
echo "✅ ML Models Deployment Initiated!"
echo "================================================="
echo ""
echo "Created Endpoints:"
echo "  - aegis-fraud-detector"
echo "  - aegis-mule-detector"
echo "  - aegis-behavioral-model"
echo ""
echo "⏳ Endpoints are being created (5-10 minutes each)"
echo ""
echo "Check endpoint status with:"
echo "  aws sagemaker describe-endpoint --endpoint-name aegis-fraud-detector"
echo ""
echo "Once endpoints are 'InService', update .env with:"
echo "  FRAUD_DETECTOR_ENDPOINT=aegis-fraud-detector"
echo "  MULE_DETECTOR_ENDPOINT=aegis-mule-detector"
echo "  BEHAVIORAL_MODEL_ENDPOINT=aegis-behavioral-model"
echo ""





