"""
Setup Bedrock Knowledge Base for RAG functionality
"""

import boto3
import os
import json
import time
from pathlib import Path
from typing import List, Dict

# AWS configuration
REGION = os.getenv('AWS_REGION', 'us-east-1')
ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
BEDROCK_EMBEDDING_MODEL_ID = os.getenv('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v2:0')
KB_BUCKET = os.getenv('KB_BUCKET', f'aegis-knowledge-base-{ACCOUNT_ID}')
KB_NAME = 'aegis-fraud-intelligence-kb'
KB_DESCRIPTION = 'Fraud typologies, investigation procedures, and regulatory guidance for APP fraud prevention'

# Initialize clients
s3_client = boto3.client('s3', region_name=REGION)
bedrock_agent_client = boto3.client('bedrock-agent', region_name=REGION)
iam_client = boto3.client('iam')

def create_kb_bucket():
    """Create S3 bucket for Knowledge Base documents."""
    
    print(f"\n📦 Creating S3 bucket: {KB_BUCKET}")
    
    try:
        if REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=KB_BUCKET)
        else:
            s3_client.create_bucket(
                Bucket=KB_BUCKET,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        
        print(f"✅ Bucket created: {KB_BUCKET}")
    except s3_client.exceptions.BucketAlreadyExists:
        print(f"ℹ️  Bucket already exists: {KB_BUCKET}")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"ℹ️  Bucket already owned by you: {KB_BUCKET}")


def upload_documents():
    """Upload documents from knowledge_base_docs/ to S3."""
    
    print("\n📄 Uploading documents to S3...")
    
    docs_dir = Path(__file__).parent.parent.parent / 'knowledge_base_docs'
    
    if not docs_dir.exists():
        print(f"⚠️  Documents directory not found: {docs_dir}")
        print("   Creating sample documents...")
        create_sample_documents(docs_dir)
    
    uploaded_count = 0
    
    for file_path in docs_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.txt', '.pdf', '.md', '.docx']:
            s3_key = f'documents/{file_path.relative_to(docs_dir)}'
            
            print(f"  ⬆️  Uploading: {file_path.name} -> {s3_key}")
            
            with open(file_path, 'rb') as f:
                s3_client.put_object(
                    Bucket=KB_BUCKET,
                    Key=s3_key,
                    Body=f.read(),
                    ContentType=get_content_type(file_path.suffix)
                )
            
            uploaded_count += 1
    
    print(f"✅ Uploaded {uploaded_count} documents")
    return uploaded_count


def create_sample_documents(docs_dir: Path):
    """Create sample fraud intelligence documents."""
    
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    documents = {
        'fraud_typologies.md': """# APP Fraud Typologies

## 1. Impersonation Scams

### Bank Impersonation
Fraudsters pose as bank officials, claiming suspicious activity and requesting immediate money transfers to "safe accounts".

**Red Flags:**
- Urgent requests to move money
- Claims of account compromises
- Pressure tactics
- Active phone calls during transactions

### Police/Authority Impersonation
Scammers impersonate law enforcement, claiming victim is under investigation.

**Red Flags:**
- Threats of arrest or legal action
- Requests for payment to "verify innocence"
- Secrecy demands
- Government official impersonation

## 2. Investment Fraud

Promises of high returns on investments in cryptocurrency, forex, or other schemes.

**Red Flags:**
- Guaranteed returns
- Pressure to invest quickly
- Unlicensed operators
- Difficulty withdrawing funds

## 3. Romance Scams

Building fake relationships to manipulate victims into sending money.

**Red Flags:**
- Quick emotional connection
- Never meeting in person
- Repeated financial emergencies
- Requests for money transfers

## 4. Invoice Redirection

Fraudsters intercept business communications and redirect invoice payments.

**Red Flags:**
- Last-minute bank detail changes
- Unusual payment request formats
- Pressure for urgent payment
- Email domain variations

## 5. Purchase Scams

Fake listings for goods/services that don't exist.

**Red Flags:**
- Too-good-to-be-true prices
- Requests for payment outside platform
- No seller verification
- Pressure to pay immediately
""",

        'investigation_procedures.md': """# Investigation Procedures

## Standard Operating Procedures for APP Fraud Investigation

### 1. Initial Assessment (0-5 minutes)

**Actions:**
1. Review automated risk score and reason codes
2. Check customer vulnerability indicators
3. Verify payee details via CoP
4. Review transaction velocity patterns
5. Check for active phone call indicator

**Decision Points:**
- Risk score > 80: Immediate escalation
- Active call detected: Priority investigation
- New payee + large amount: Enhanced verification

### 2. Customer Verification (5-15 minutes)

**Actions:**
1. Contact customer via verified channel
2. Verify recent transaction intent
3. Ask open-ended questions about payment purpose
4. Assess customer awareness of scam risks
5. Educate about common fraud patterns

**Red Flags:**
- Customer under duress
- Vague payment explanations
- Resistance to questions
- Unusual urgency

### 3. Payee Investigation (10-20 minutes)

**Actions:**
1. Check payee account history
2. Review network relationships
3. Identify mule account indicators
4. Check sanctions/watchlists
5. Analyze transaction patterns

**Mule Indicators:**
- Fan-in/fan-out patterns
- Rapid money movement
- New account with high activity
- Multiple unique senders/receivers

### 4. Evidence Collection

**Required Documentation:**
1. Transaction timeline
2. Customer communication records
3. Network analysis results
4. ML model outputs and SHAP explanations
5. Analyst reasoning and decision rationale

### 5. Decision Making

**Outcomes:**
- **Allow**: Low risk, proceed with transaction
- **Challenge**: Medium risk, customer dialogue required
- **Block**: High risk, transaction stopped and escalated

**Post-Decision:**
- Document case in system
- If blocked, prepare SAR if required
- Monitor for follow-up attempts
""",

        'regulatory_requirements.md': """# Regulatory Requirements

## UK Money Laundering Regulations 2017

### Suspicious Activity Reports (SAR)

**When to File:**
- Knowledge or suspicion of money laundering
- Reasonable grounds for knowledge or suspicion
- All attempted and completed suspicious transactions

**Filing Deadline:**
- As soon as practicable after suspicion arises
- Typically within 30 days

**Required Information:**
1. Subject details (customer and beneficiary)
2. Detailed narrative of suspicious activity
3. Transaction information and amounts
4. Rationale for suspicion
5. Supporting evidence

### Proceeds of Crime Act (POCA) 2002

**Key Obligations:**
- Report suspicious activity to NCA
- Obtain consent before proceeding with suspicious transactions
- Maintain records for 7 years
- Staff training on money laundering risks

### Payment Services Regulations (PSR)

**Strong Customer Authentication:**
- Required for electronic payments
- Exemptions for low-risk transactions
- Fraud liability considerations

**Confirmation of Payee (CoP):**
- Mandatory checks before payment
- Name matching requirements
- Disclosure obligations

### Data Protection (GDPR)

**PII Handling:**
- Lawful basis for processing
- Data minimization
- Encryption requirements
- Right to be forgotten (with exceptions)

### Bias and Fairness

**Requirements:**
- No discrimination based on protected characteristics
- Regular bias monitoring
- Explainable decision-making
- Human oversight for high-risk cases
""",

        'mule_detection_patterns.md': """# Money Mule Detection Patterns

## Network Patterns Indicating Mule Activity

### 1. Fan-Out Pattern
Single source account dispersing funds to many recipients.

**Characteristics:**
- 1 sender -> 10+ receivers
- Short time intervals
- Similar amounts
- New payees

**Risk Level:** HIGH

### 2. Fan-In Pattern  
Multiple senders to single receiver (classic mule indicator).

**Characteristics:**
- 10+ senders -> 1 receiver
- Rapid accumulation
- Quick onward movement
- New account

**Risk Level:** CRITICAL

### 3. Circular Flows
Funds flowing in loops through intermediaries.

**Characteristics:**
- Money returns to origin
- 3+ intermediaries
- Layering technique
- Complex routing

**Risk Level:** HIGH

### 4. Rapid Movement
Funds move through account quickly without accumulation.

**Characteristics:**
- In and out within hours
- No balance retention
- High velocity
- Automated patterns

**Risk Level:** CRITICAL

### 5. Intermediary Behavior
Account acts as conduit between source and destination.

**Characteristics:**
- Consistent pass-through
- No personal use
- Transaction pairs (in/out)
- Network centrality

**Risk Level:** HIGH

## GNN Detection Features

1. **In-Degree**: Number of incoming connections
2. **Out-Degree**: Number of outgoing connections
3. **Betweenness Centrality**: Bridge position in network
4. **Transaction Velocity**: Speed of money movement
5. **Account Age**: New accounts more suspicious
6. **Amount Patterns**: Consistent or structured amounts
"""
    }
    
    for filename, content in documents.items():
        file_path = docs_dir / filename
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✅ Created: {filename}")


def create_kb_role():
    """Create IAM role for Bedrock Knowledge Base."""
    
    print("\n🔐 Creating IAM role for Knowledge Base...")
    
    role_name = 'AegisBedrockKBRole'
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "bedrock.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Aegis Bedrock Knowledge Base'
        )
        role_arn = response['Role']['Arn']
        print(f"✅ Role created: {role_arn}")
        
        # Attach policies
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{KB_BUCKET}",
                        f"arn:aws:s3:::{KB_BUCKET}/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel"
                    ],
                    "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='AegisKBPolicy',
            PolicyDocument=json.dumps(policy_document)
        )
        
        print("✅ Policies attached")
        
        # Wait for role to propagate
        time.sleep(10)
        
        return role_arn
    
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"ℹ️  Role already exists: {role_name}")
        response = iam_client.get_role(RoleName=role_name)
        return response['Role']['Arn']


def create_knowledge_base(role_arn: str):
    """Create Bedrock Knowledge Base."""
    
    print(f"\n🧠 Creating Bedrock Knowledge Base: {KB_NAME}")
    
    try:
        response = bedrock_agent_client.create_knowledge_base(
            name=KB_NAME,
            description=KB_DESCRIPTION,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': f'arn:aws:bedrock:{REGION}::foundation-model/amazon.titan-embed-text-v2:0'
                }
            },
            storageConfiguration={
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': f'arn:aws:aoss:{REGION}:{ACCOUNT_ID}:collection/aegis-kb',
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
        print(f"✅ Knowledge Base created: {kb_id}")
        
        return kb_id
    
    except Exception as e:
        print(f"❌ Failed to create Knowledge Base: {e}")
        print("   Note: Requires OpenSearch Serverless collection to be created first")
        return None


def create_data_source(kb_id: str):
    """Create data source for Knowledge Base."""
    
    print("\n📊 Creating data source...")
    
    try:
        response = bedrock_agent_client.create_data_source(
            knowledgeBaseId=kb_id,
            name='aegis-s3-documents',
            description='S3 bucket containing fraud intelligence documents',
            dataSourceConfiguration={
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f'arn:aws:s3:::{KB_BUCKET}',
                    'inclusionPrefixes': ['documents/']
                }
            }
        )
        
        data_source_id = response['dataSource']['dataSourceId']
        print(f"✅ Data source created: {data_source_id}")
        
        return data_source_id
    
    except Exception as e:
        print(f"❌ Failed to create data source: {e}")
        return None


def ingest_documents(kb_id: str, data_source_id: str):
    """Start ingestion job to index documents."""
    
    print("\n🔄 Starting document ingestion...")
    
    try:
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        ingestion_job_id = response['ingestionJob']['ingestionJobId']
        print(f"✅ Ingestion job started: {ingestion_job_id}")
        
        # Wait for completion
        print("⏳ Waiting for ingestion to complete...")
        
        while True:
            status_response = bedrock_agent_client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=ingestion_job_id
            )
            
            status = status_response['ingestionJob']['status']
            
            if status == 'COMPLETE':
                print("✅ Ingestion complete!")
                break
            elif status == 'FAILED':
                print("❌ Ingestion failed")
                break
            else:
                print(f"   Status: {status}...")
                time.sleep(10)
        
        return ingestion_job_id
    
    except Exception as e:
        print(f"❌ Failed to start ingestion: {e}")
        return None


def test_knowledge_base(kb_id: str):
    """Test querying the Knowledge Base."""
    
    print("\n🧪 Testing Knowledge Base queries...")
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)
    
    test_queries = [
        "What are the indicators of impersonation fraud?",
        "How do I detect mule accounts?",
        "What are the regulatory requirements for SAR filing?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        try:
            response = bedrock_agent_runtime.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': 3
                    }
                }
            )
            
            for i, result in enumerate(response.get('retrievalResults', []), 1):
                content = result['content']['text'][:200] + '...'
                score = result.get('score', 0)
                print(f"  Result {i} (score: {score:.2f}): {content}")
        
        except Exception as e:
            print(f"  ❌ Query failed: {e}")


def get_content_type(suffix: str) -> str:
    """Get MIME type for file suffix."""
    types = {
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    return types.get(suffix, 'application/octet-stream')


def main():
    """Main setup function."""
    
    print("=" * 60)
    print("AEGIS BEDROCK KNOWLEDGE BASE SETUP")
    print("=" * 60)
    
    if not ACCOUNT_ID:
        print("❌ Error: AWS_ACCOUNT_ID not set")
        print("   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)")
        return
    
    print(f"\n📍 Region: {REGION}")
    print(f"🆔 Account: {ACCOUNT_ID}")
    print(f"📦 Bucket: {KB_BUCKET}")
    
    try:
        # Step 1: Create S3 bucket
        create_kb_bucket()
        
        # Step 2: Upload documents
        doc_count = upload_documents()
        
        if doc_count == 0:
            print("⚠️  No documents uploaded, cannot proceed")
            return
        
        # Step 3: Create IAM role
        # role_arn = create_kb_role()
        
        # Step 4: Create Knowledge Base (requires OpenSearch Serverless)
        print("\n⚠️  Note: Creating Knowledge Base requires OpenSearch Serverless collection")
        print("   Run: aws opensearchserverless create-collection --name aegis-kb --type VECTORSEARCH")
        
        # Uncomment when OpenSearch collection is ready:
        # kb_id = create_knowledge_base(role_arn)
        # if kb_id:
        #     data_source_id = create_data_source(kb_id)
        #     if data_source_id:
        #         ingest_documents(kb_id, data_source_id)
        #         test_knowledge_base(kb_id)
        
        print("\n" + "=" * 60)
        print("✅ KNOWLEDGE BASE SETUP COMPLETE (S3 & Documents)")
        print("=" * 60)
        
        print("\n📝 Next steps:")
        print("  1. Create OpenSearch Serverless collection:")
        print(f"     aws opensearchserverless create-collection --name aegis-kb --type VECTORSEARCH --region {REGION}")
        print("  2. Uncomment Knowledge Base creation in this script")
        print("  3. Run script again to create KB and ingest documents")
        print("  4. Update backend/config/system_config.py with KB ID")
        print("  5. Test with: backend/agents/analysis/intel_agent.py")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        raise


if __name__ == '__main__':
    main()

