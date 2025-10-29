"""AWS service clients configuration for Aegis platform."""

import os
import boto3
from typing import Optional

class AWSConfig:
    """Centralized AWS service clients and configuration."""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.account_id = os.getenv('AWS_ACCOUNT_ID')
        
        # Initialize clients
        self._bedrock_runtime = None
        self._bedrock_agent_runtime = None
        self._dynamodb = None
        self._s3 = None
        self._sagemaker_runtime = None
        self._neptune = None
        self._cloudwatch = None
        self._xray = None
        self._secrets_manager = None
        self._cognito = None
        self._eventbridge = None
    
    @property
    def bedrock_runtime(self):
        """Bedrock Runtime client for model invocations."""
        if not self._bedrock_runtime:
            self._bedrock_runtime = boto3.client('bedrock-runtime', region_name=self.region)
        return self._bedrock_runtime
    
    @property
    def bedrock_agent_runtime(self):
        """Bedrock Agent Runtime for Knowledge Base queries."""
        if not self._bedrock_agent_runtime:
            self._bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
        return self._bedrock_agent_runtime
    
    @property
    def dynamodb(self):
        """DynamoDB client for case storage and transactions."""
        if not self._dynamodb:
            self._dynamodb = boto3.resource('dynamodb', region_name=self.region)
        return self._dynamodb
    
    @property
    def s3(self):
        """S3 client for document storage and model artifacts."""
        if not self._s3:
            self._s3 = boto3.client('s3', region_name=self.region)
        return self._s3
    
    @property
    def sagemaker_runtime(self):
        """SageMaker Runtime for ML model inference."""
        if not self._sagemaker_runtime:
            self._sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=self.region)
        return self._sagemaker_runtime
    
    @property
    def cloudwatch(self):
        """CloudWatch client for metrics and monitoring."""
        if not self._cloudwatch:
            self._cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        return self._cloudwatch
    
    @property
    def xray(self):
        """X-Ray client for distributed tracing."""
        if not self._xray:
            self._xray = boto3.client('xray', region_name=self.region)
        return self._xray
    
    @property
    def secrets_manager(self):
        """Secrets Manager for API keys and credentials."""
        if not self._secrets_manager:
            self._secrets_manager = boto3.client('secretsmanager', region_name=self.region)
        return self._secrets_manager
    
    @property
    def cognito(self):
        """Cognito client for user authentication."""
        if not self._cognito:
            self._cognito = boto3.client('cognito-idp', region_name=self.region)
        return self._cognito
    
    @property
    def eventbridge(self):
        """EventBridge client for event orchestration."""
        if not self._eventbridge:
            self._eventbridge = boto3.client('events', region_name=self.region)
        return self._eventbridge

# Global AWS config instance
aws_config = AWSConfig()



