"""Fetch AWS Resource IDs and Update .env File"""

import boto3
import os
import re
from pathlib import Path
from typing import Dict, Optional

def get_aws_account_id() -> str:
    """Get AWS Account ID"""
    sts = boto3.client('sts')
    return sts.get_caller_identity()['Account']

def get_s3_buckets(account_id: str) -> Dict[str, str]:
    """Get S3 bucket names"""
    return {
        'ML_MODELS_BUCKET': f'aegis-ml-models-{account_id}',
        'DOCUMENTS_BUCKET': f'aegis-kb-documents-{account_id}',
        'DATA_BUCKET': f'aegis-data-{account_id}'
    }

def get_dynamodb_tables() -> Dict[str, str]:
    """Get DynamoDB table names"""
    return {
        'CASES_TABLE': 'aegis-cases',
        'TRANSACTIONS_TABLE': 'aegis-transactions',
        'CUSTOMERS_TABLE': 'aegis-customers',
        'AUDIT_LOGS_TABLE': 'aegis-audit-logs'
    }

def get_cognito_ids(region: str) -> Dict[str, str]:
    """Get Cognito User Pool and Client IDs"""
    cognito = boto3.client('cognito-idp', region_name=region)
    
    # Get user pool ID
    pools = cognito.list_user_pools(MaxResults=10)
    pool_id = None
    for pool in pools.get('UserPools', []):
        if pool['Name'] == 'aegis-users':
            pool_id = pool['Id']
            break
    
    # Get client ID
    client_id = None
    if pool_id:
        clients = cognito.list_user_pool_clients(
            UserPoolId=pool_id,
            MaxResults=10
        )
        for client in clients.get('UserPoolClients', []):
            if client['ClientName'] == 'aegis-web-client':
                client_id = client['ClientId']
                break
    
    return {
        'COGNITO_USER_POOL_ID': pool_id or '',
        'COGNITO_CLIENT_ID': client_id or ''
    }

def get_bedrock_guardrails(region: str) -> Dict[str, str]:
    """Get Bedrock Guardrail IDs"""
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        
        # List guardrails
        guardrails = bedrock.list_guardrails()
        
        input_guardrail_id = None
        output_guardrail_id = None
        
        for guardrail in guardrails.get('guardrails', []):
            if guardrail.get('name') == 'AegisInputGuardrails':
                input_guardrail_id = guardrail.get('id')
            elif guardrail.get('name') == 'AegisOutputGuardrails':
                output_guardrail_id = guardrail.get('id')
        
        return {
            'INPUT_GUARDRAILS_ID': input_guardrail_id or '',
            'DIALOGUE_GUARDRAILS_ID': output_guardrail_id or ''
        }
    except Exception as e:
        print(f"Warning: Could not fetch Bedrock Guardrails: {e}")
        return {
            'INPUT_GUARDRAILS_ID': '',
            'DIALOGUE_GUARDRAILS_ID': ''
        }

def get_bedrock_knowledge_base(region: str) -> Optional[str]:
    """Get Bedrock Knowledge Base ID"""
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        
        # List knowledge bases
        kbs = bedrock_agent.list_knowledge_bases()
        
        for kb in kbs.get('knowledgeBaseSummaries', []):
            if kb.get('name') == 'aegis-fraud-intelligence':
                return kb.get('knowledgeBaseId')
        
        return None
    except Exception as e:
        print(f"Warning: Could not fetch Knowledge Base ID: {e}")
        return None

def get_sagemaker_endpoints(region: str) -> Dict[str, str]:
    """Get SageMaker endpoint names"""
    try:
        sagemaker = boto3.client('sagemaker', region_name=region)
        
        endpoints = {}
        endpoint_names = [
            'aegis-fraud-detector',
            'aegis-mule-detector',
            'aegis-behavioral-model',
            'aegis-anomaly-detector'
        ]
        
        for name in endpoint_names:
            try:
                sagemaker.describe_endpoint(EndpointName=name)
                key = name.replace('aegis-', '').replace('-', '_').upper() + '_ENDPOINT'
                endpoints[key] = name
            except sagemaker.exceptions.ClientError:
                # Endpoint doesn't exist
                pass
        
        return endpoints
    except Exception as e:
        print(f"Warning: Could not fetch SageMaker endpoints: {e}")
        return {}

def update_env_file(resources: Dict[str, str], env_path: Path):
    """Update .env file with fetched resources"""
    
    # Read existing .env or template
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
    elif env_path.with_suffix('.template').exists():
        with open(env_path.with_suffix('.template'), 'r') as f:
            content = f.read()
    else:
        print("Error: No .env or env.template file found")
        return
    
    # Update each resource
    for key, value in resources.items():
        if value:  # Only update if value exists
            # Pattern to match the line with the key
            pattern = rf'^{key}=.*$'
            replacement = f'{key}={value}'
            
            if re.search(pattern, content, re.MULTILINE):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                print(f"✓ Updated {key}={value}")
            else:
                # Add new line if key doesn't exist
                content += f'\n{replacement}\n'
                print(f"✓ Added {key}={value}")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(content)
    
    print(f"\n✓ Updated {env_path}")

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║     Fetching AWS Resource IDs                               ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Get AWS region from environment or default
    region = os.environ.get('AWS_REGION', 'us-east-1')
    print(f"AWS Region: {region}\n")
    
    # Get account ID
    print("Fetching AWS Account ID...")
    account_id = get_aws_account_id()
    print(f"✓ Account ID: {account_id}\n")
    
    # Collect all resources
    resources = {
        'AWS_ACCOUNT_ID': account_id,
        'AWS_REGION': region
    }
    
    print("Fetching S3 bucket names...")
    resources.update(get_s3_buckets(account_id))
    
    print("Fetching DynamoDB table names...")
    resources.update(get_dynamodb_tables())
    
    print("Fetching Cognito IDs...")
    cognito_ids = get_cognito_ids(region)
    resources.update(cognito_ids)
    
    print("Fetching Bedrock Guardrails...")
    resources.update(get_bedrock_guardrails(region))
    
    print("Fetching Bedrock Knowledge Base...")
    kb_id = get_bedrock_knowledge_base(region)
    if kb_id:
        resources['KNOWLEDGE_BASE_ID'] = kb_id
    
    print("Fetching SageMaker endpoints...")
    resources.update(get_sagemaker_endpoints(region))
    
    # Add Bedrock model IDs
    resources.update({
        'BEDROCK_MODEL_ID': 'global.anthropic.claude-sonnet-4-20250514-v1:0',
        'BEDROCK_EMBEDDING_MODEL_ID': 'amazon.titan-embed-text-v2:0'
    })
    
    print("\n" + "="*60)
    print("Fetched Resources:")
    print("="*60)
    for key, value in sorted(resources.items()):
        if value:
            print(f"  {key}: {value}")
    print("="*60 + "\n")
    
    # Update .env file
    env_path = Path(__file__).parent.parent.parent / '.env'
    update_env_file(resources, env_path)
    
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║     ✓ Resource IDs Fetched and Updated!                    ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("Next steps:")
    print("  1. Review .env file for completeness")
    print("  2. Run: python datasets/aegis_datasets/populate_aws.py")
    print()

if __name__ == '__main__':
    main()





