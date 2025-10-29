"""Setup AWS Bedrock Knowledge Base."""

import boto3
import os
import sys

def create_knowledge_base():
    """Create Bedrock Knowledge Base with OpenSearch Serverless."""
    
    bedrock = boto3.client('bedrock-agent')
    s3 = boto3.client('s3')
    
    account_id = os.getenv('AWS_ACCOUNT_ID')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    # S3 bucket for documents
    bucket_name = f'aegis-kb-documents-{account_id}'
    
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✓ Created S3 bucket: {bucket_name}")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ S3 bucket already exists: {bucket_name}")
    
    # Create Knowledge Base
    try:
        response = bedrock.create_knowledge_base(
            name='aegis-fraud-kb',
            description='Fraud typologies, SOPs, and regulatory guidance for Aegis platform',
            roleArn=f'arn:aws:iam::{account_id}:role/AegisKnowledgeBaseRole',
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': f'arn:aws:aoss:{region}:{account_id}:collection/aegis-kb',
                    'vectorIndexName': 'aegis-fraud-index',
                    'fieldMapping': {
                        'vectorField': 'embedding',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        print(f"✓ Created Knowledge Base: {kb_id}")
        print(f"\nAdd this to your .env file:")
        print(f"KNOWLEDGE_BASE_ID={kb_id}")
        
        return kb_id
    
    except Exception as e:
        print(f"✗ Failed to create Knowledge Base: {e}")
        print("\nNote: You may need to:")
        print("1. Create OpenSearch Serverless collection first")
        print("2. Create IAM role: AegisKnowledgeBaseRole")
        print("3. Grant necessary permissions")
        return None

if __name__ == '__main__':
    create_knowledge_base()

