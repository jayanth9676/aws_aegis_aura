"""Populate Knowledge Base with documents."""

import boto3
import os
from pathlib import Path

def upload_documents():
    """Upload documents from knowledge_base_docs/ to S3."""
    
    s3 = boto3.client('s3')
    bedrock = boto3.client('bedrock-agent')
    
    account_id = os.getenv('AWS_ACCOUNT_ID')
    kb_id = os.getenv('KNOWLEDGE_BASE_ID')
    bucket_name = f'aegis-kb-documents-{account_id}'
    
    if not kb_id:
        print("✗ KNOWLEDGE_BASE_ID not set in environment")
        print("Run setup.py first and add KNOWLEDGE_BASE_ID to .env")
        return
    
    # Upload documents
    docs_dir = Path('knowledge_base_docs')
    uploaded = 0
    
    for file_path in docs_dir.rglob('*.md'):
        relative_path = file_path.relative_to(docs_dir)
        s3_key = f'knowledge-base/{relative_path}'
        
        try:
            s3.upload_file(
                str(file_path),
                bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'text/markdown'}
            )
            print(f"✓ Uploaded: {relative_path}")
            uploaded += 1
        except Exception as e:
            print(f"✗ Failed to upload {relative_path}: {e}")
    
    print(f"\n✓ Uploaded {uploaded} documents to S3")
    
    # Create Data Source
    try:
        response = bedrock.create_data_source(
            knowledgeBaseId=kb_id,
            name='aegis-fraud-documents',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{bucket_name}',
                    'inclusionPrefixes': ['knowledge-base/']
                }
            }
        )
        
        data_source_id = response['dataSource']['dataSourceId']
        print(f"✓ Created Data Source: {data_source_id}")
        
        # Start ingestion job
        ingestion = bedrock.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        print(f"✓ Started ingestion job: {ingestion['ingestionJob']['ingestionJobId']}")
        print("\nDocuments are being indexed. This may take 5-10 minutes.")
        print("Check status in AWS Console: Bedrock → Knowledge Bases")
    
    except Exception as e:
        print(f"✗ Failed to create data source: {e}")

if __name__ == '__main__':
    upload_documents()

