"""Populate AWS Services with Aegis Datasets"""

import boto3
import json
import os
from decimal import Decimal
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import time

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def convert_floats_to_decimal(obj: Any) -> Any:
    """Convert floats to Decimal for DynamoDB"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

def load_json_dataset(file_path: Path) -> Dict:
    """Load JSON dataset file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def populate_dynamodb_table(table_name: str, items: List[Dict], key_field: str, region: str):
    """Populate DynamoDB table with items"""
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    
    print(f"\nPopulating {table_name}...")
    
    success_count = 0
    error_count = 0
    
    # Batch write items (max 25 per batch)
    with table.batch_writer() as batch:
        for i, item in enumerate(items):
            try:
                # Convert floats to Decimal
                item_converted = convert_floats_to_decimal(item)
                batch.put_item(Item=item_converted)
                success_count += 1
                
                if (i + 1) % 100 == 0:
                    print(f"  Loaded {i + 1}/{len(items)} items...")
            except Exception as e:
                print(f"  Error loading item {item.get(key_field, 'unknown')}: {e}")
                error_count += 1
    
    print(f"✓ {table_name}: {success_count} items loaded, {error_count} errors")
    return success_count, error_count

def populate_customers(data_dir: Path, region: str):
    """Populate customers table"""
    dataset = load_json_dataset(data_dir / 'aegis_customers.json')
    customers = dataset.get('customers', [])
    
    return populate_dynamodb_table(
        'aegis-customers',
        customers,
        'customer_id',
        region
    )

def populate_transactions(data_dir: Path, region: str):
    """Populate transactions table"""
    dataset = load_json_dataset(data_dir / 'aegis_transactions.json')
    transactions = dataset.get('transactions', [])
    
    return populate_dynamodb_table(
        'aegis-transactions',
        transactions,
        'transaction_id',
        region
    )

def populate_cases(data_dir: Path, region: str):
    """Populate cases table"""
    dataset = load_json_dataset(data_dir / 'aegis_cases.json')
    cases = dataset.get('cases', [])
    
    return populate_dynamodb_table(
        'aegis-cases',
        cases,
        'case_id',
        region
    )

def create_audit_logs(data_dir: Path, region: str):
    """Create initial audit logs from dataset actions"""
    print("\nCreating audit logs...")
    
    # Load cases to create audit entries
    cases_data = load_json_dataset(data_dir / 'aegis_cases.json')
    cases = cases_data.get('cases', [])
    
    audit_logs = []
    for case in cases[:100]:  # Create audit logs for first 100 cases
        audit_log = {
            'id': f"AUDIT-{case['case_id']}-001",
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'CASE_CREATED',
            'case_id': case['case_id'],
            'customer_id': case['customer_id'],
            'transaction_id': case['transaction_id'],
            'analyst_id': case.get('assigned_analyst_id', 'SYSTEM'),
            'details': {
                'case_type': case['case_type'],
                'priority': case['priority'],
                'risk_score': case.get('risk_score', 0)
            }
        }
        audit_logs.append(audit_log)
    
    return populate_dynamodb_table(
        'aegis-audit-logs',
        audit_logs,
        'id',
        region
    )

def upload_datasets_to_s3(data_dir: Path, bucket_name: str, region: str):
    """Upload all datasets to S3 for ML training and backup"""
    s3 = boto3.client('s3', region_name=region)
    
    print(f"\nUploading datasets to S3 bucket: {bucket_name}...")
    
    dataset_files = [
        'aegis_customers.json',
        'aegis_accounts.json',
        'aegis_transactions.json',
        'aegis_cases.json',
        'aegis_devices.json',
        'aegis_payees.json',
        'aegis_behavioral_events.json',
        'aegis_fraud_alerts.json',
        'aegis_call_history.json',
        'aegis_graph_relationships.json'
    ]
    
    uploaded = 0
    for filename in dataset_files:
        file_path = data_dir / filename
        if file_path.exists():
            try:
                s3_key = f'datasets/{filename}'
                s3.upload_file(
                    str(file_path),
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ServerSideEncryption': 'AES256'}
                )
                print(f"  ✓ Uploaded {filename}")
                uploaded += 1
            except Exception as e:
                print(f"  ✗ Error uploading {filename}: {e}")
    
    print(f"✓ Uploaded {uploaded}/{len(dataset_files)} datasets to S3")
    return uploaded

def create_ml_training_dataset(data_dir: Path, bucket_name: str, region: str):
    """Create ML training dataset from transactions and upload to S3"""
    print("\nCreating ML training dataset...")
    
    # Load transactions
    transactions_data = load_json_dataset(data_dir / 'aegis_transactions.json')
    transactions = transactions_data.get('transactions', [])
    
    # Extract ML features
    ml_dataset = []
    for txn in transactions:
        ml_record = {
            'transaction_id': txn['transaction_id'],
            'amount': txn['amount'],
            'risk_score': txn.get('risk_score', 0),
            'location_risk': txn.get('location_risk', 0),
            'amount_risk': txn.get('amount_risk', 0),
            'velocity_risk': txn.get('velocity_risk', 0),
            'device_trust_score': txn.get('device_trust_score', 1.0),
            'known_device': 1 if txn.get('known_device') else 0,
            'is_fraud': 1 if txn.get('is_fraud') else 0,
            'fraud_type': txn.get('fraud_type', ''),
            'ml_fraud_probability': txn.get('ml_fraud_probability', 0.0)
        }
        ml_dataset.append(ml_record)
    
    # Save to JSON
    ml_file = data_dir / 'ml_training_data.json'
    with open(ml_file, 'w') as f:
        json.dump({'records': ml_dataset}, f, indent=2, cls=DecimalEncoder)
    
    # Upload to S3
    s3 = boto3.client('s3', region_name=region)
    try:
        s3.upload_file(
            str(ml_file),
            bucket_name,
            'ml-training/fraud_detection_training.json',
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )
        print(f"✓ Created and uploaded ML training dataset ({len(ml_dataset)} records)")
    except Exception as e:
        print(f"✗ Error uploading ML training dataset: {e}")

def verify_data_integrity(data_dir: Path, region: str):
    """Verify data integrity in DynamoDB"""
    print("\n" + "="*60)
    print("Verifying Data Integrity")
    print("="*60)
    
    dynamodb = boto3.client('dynamodb', region_name=region)
    
    tables = {
        'aegis-customers': 100,      # Expected ~100 customers
        'aegis-transactions': 3208,  # Expected ~3208 transactions
        'aegis-cases': 267,          # Expected ~267 cases
        'aegis-audit-logs': 100      # Expected ~100 audit logs
    }
    
    for table_name, expected_count in tables.items():
        try:
            response = dynamodb.describe_table(TableName=table_name)
            item_count = response['Table']['ItemCount']
            
            status = "✓" if item_count >= expected_count * 0.9 else "⚠"
            print(f"{status} {table_name}: {item_count} items (expected ~{expected_count})")
        except Exception as e:
            print(f"✗ {table_name}: Error - {e}")

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║     Populating AWS Services with Aegis Datasets             ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Get configuration from environment
    region = os.environ.get('AWS_REGION', 'us-east-1')
    account_id = os.environ.get('AWS_ACCOUNT_ID')
    
    if not account_id:
        # Try to get from AWS
        sts = boto3.client('sts')
        account_id = sts.get_caller_identity()['Account']
    
    data_bucket = os.environ.get('DATA_BUCKET', f'aegis-data-{account_id}')
    
    print(f"AWS Region: {region}")
    print(f"AWS Account: {account_id}")
    print(f"Data Bucket: {data_bucket}")
    print()
    
    # Get dataset directory
    data_dir = Path(__file__).parent
    
    # Verify dataset files exist
    required_files = [
        'aegis_customers.json',
        'aegis_transactions.json',
        'aegis_cases.json'
    ]
    
    missing_files = []
    for filename in required_files:
        if not (data_dir / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        print(f"Error: Missing required dataset files: {', '.join(missing_files)}")
        print("Please run: python generate_aegis_datasets.py")
        return
    
    # Track statistics
    stats = {
        'customers': 0,
        'transactions': 0,
        'cases': 0,
        'audit_logs': 0,
        's3_files': 0
    }
    
    try:
        # Populate DynamoDB tables
        print("="*60)
        print("Populating DynamoDB Tables")
        print("="*60)
        
        stats['customers'], _ = populate_customers(data_dir, region)
        stats['transactions'], _ = populate_transactions(data_dir, region)
        stats['cases'], _ = populate_cases(data_dir, region)
        stats['audit_logs'], _ = create_audit_logs(data_dir, region)
        
        # Upload to S3
        print("\n" + "="*60)
        print("Uploading to S3")
        print("="*60)
        
        stats['s3_files'] = upload_datasets_to_s3(data_dir, data_bucket, region)
        create_ml_training_dataset(data_dir, data_bucket, region)
        
        # Verify integrity
        time.sleep(2)  # Wait for DynamoDB to update counts
        verify_data_integrity(data_dir, region)
        
        # Summary
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║     ✓ AWS Population Complete!                              ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print("Summary:")
        print(f"  Customers loaded: {stats['customers']}")
        print(f"  Transactions loaded: {stats['transactions']}")
        print(f"  Cases loaded: {stats['cases']}")
        print(f"  Audit logs created: {stats['audit_logs']}")
        print(f"  Datasets uploaded to S3: {stats['s3_files']}")
        print()
        print("Next steps:")
        print("  1. Verify data in AWS Console")
        print("  2. Configure AgentCore Runtime")
        print("  3. Deploy Lambda functions for tools")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during population: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()





