"""Create DynamoDB tables for Aegis platform."""

import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='us-east-1')

def create_cases_table():
    """Create aegis-cases table."""
    print("Creating aegis-cases table...")
    
    try:
        dynamodb.create_table(
            TableName='aegis-cases',
            KeySchema=[
                {'AttributeName': 'case_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'case_id', 'AttributeType': 'S'},
                {'AttributeName': 'customer_id', 'AttributeType': 'S'},
                {'AttributeName': 'created_date', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'priority', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'customer-cases-index',
                    'KeySchema': [
                        {'AttributeName': 'customer_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_date', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'status-priority-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'priority', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        
        print("  ✓ aegis-cases table creation initiated")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("  ⚠ Table already exists")
            return True
        else:
            print(f"  ✗ Error: {e}")
            return False


def create_transactions_table():
    """Create aegis-transactions table."""
    print("Creating aegis-transactions table...")
    
    try:
        dynamodb.create_table(
            TableName='aegis-transactions',
            KeySchema=[
                {'AttributeName': 'transaction_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'transaction_id', 'AttributeType': 'S'},
                {'AttributeName': 'customer_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'customer-timestamp-index',
                    'KeySchema': [
                        {'AttributeName': 'customer_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 10,
                        'WriteCapacityUnits': 10
                    }
                },
                {
                    'IndexName': 'status-timestamp-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 15,
                'WriteCapacityUnits': 15
            }
        )
        
        print("  ✓ aegis-transactions table creation initiated")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("  ⚠ Table already exists")
            return True
        else:
            print(f"  ✗ Error: {e}")
            return False


def create_customers_table():
    """Create aegis-customers table."""
    print("Creating aegis-customers table...")
    
    try:
        dynamodb.create_table(
            TableName='aegis-customers',
            KeySchema=[
                {'AttributeName': 'customer_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'customer_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        
        print("  ✓ aegis-customers table creation initiated")
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("  ⚠ Table already exists")
            return True
        else:
            print(f"  ✗ Error: {e}")
            return False


def create_audit_logs_table():
    """Create aegis-audit-logs table with TTL."""
    print("Creating aegis-audit-logs table...")
    
    try:
        dynamodb.create_table(
            TableName='aegis-audit-logs',
            KeySchema=[
                {'AttributeName': 'log_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'log_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'agent_name', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'agent-timestamp-index',
                    'KeySchema': [
                        {'AttributeName': 'agent_name', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        
        print("  ✓ aegis-audit-logs table creation initiated")
        
        # Enable TTL (7 years = 220898400 seconds)
        try:
            dynamodb.update_time_to_live(
                TableName='aegis-audit-logs',
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
            print("  ✓ TTL enabled for audit logs (7-year retention)")
        except Exception as e:
            print(f"  ⚠ TTL configuration warning: {e}")
        
        return True
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("  ⚠ Table already exists")
            return True
        else:
            print(f"  ✗ Error: {e}")
            return False


def wait_for_tables():
    """Wait for all tables to become active."""
    print("\nWaiting for tables to become ACTIVE...")
    
    tables = ['aegis-cases', 'aegis-transactions', 'aegis-customers', 'aegis-audit-logs']
    waiter = dynamodb.get_waiter('table_exists')
    
    for table_name in tables:
        try:
            print(f"  Waiting for {table_name}...", end=" ")
            waiter.wait(
                TableName=table_name,
                WaiterConfig={'Delay': 5, 'MaxAttempts': 40}
            )
            print("✓")
        except Exception as e:
            print(f"✗ {e}")


def main():
    """Main execution function."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║     AEGIS - DynamoDB Tables Creation                         ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    success = True
    
    # Create all tables
    success &= create_cases_table()
    success &= create_transactions_table()
    success &= create_customers_table()
    success &= create_audit_logs_table()
    
    if success:
        # Wait for tables to be ready
        wait_for_tables()
        
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║     ✓ All DynamoDB Tables Created Successfully               ║")
        print("║                                                              ║")
        print("║     Tables:                                                  ║")
        print("║       • aegis-cases (with 2 GSIs)                            ║")
        print("║       • aegis-transactions (with 2 GSIs)                     ║")
        print("║       • aegis-customers                                      ║")
        print("║       • aegis-audit-logs (with TTL)                          ║")
        print("║                                                              ║")
        print("║     Next Step:                                               ║")
        print("║       python infrastructure/scripts/populate_test_data.py    ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
    else:
        print("\n✗ Some tables failed to create. Check errors above.")


if __name__ == '__main__':
    main()
