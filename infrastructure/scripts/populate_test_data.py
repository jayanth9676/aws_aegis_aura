"""Populate DynamoDB with realistic test data for Aegis platform."""

import boto3
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import random
from faker import Faker

fake = Faker(['en_GB'])

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
cases_table = dynamodb.Table('aegis-cases')
transactions_table = dynamodb.Table('aegis-transactions')
customers_table = dynamodb.Table('aegis-customers')

# Helper function to convert floats to Decimal for DynamoDB
def decimal_default(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    raise TypeError


def generate_customers(count=1000):
    """Generate realistic customer profiles."""
    print(f"Generating {count} customers...")
    
    customers = []
    for i in range(count):
        customer_id = f"CUST-{str(uuid.uuid4())[:8].upper()}"
        
        customer = {
            'customer_id': customer_id,
            'personal_information': {
                'name_full': fake.name(),
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
                'age': random.randint(18, 90),
                'gender': random.choice(['M', 'F', 'Other']),
                'nationality': 'GB'
            },
            'contact_information': {
                'email_primary': fake.email(),
                'phone_mobile': fake.phone_number(),
                'address_line1': fake.street_address(),
                'city': fake.city(),
                'postcode': fake.postcode(),
                'country': 'United Kingdom'
            },
            'account_information': {
                'account_number': fake.bban(),
                'sort_code': f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}",
                'account_type': random.choice(['CURRENT', 'SAVINGS']),
                'account_opened_date': (datetime.now() - timedelta(days=random.randint(365, 3650))).isoformat()
            },
            'risk_profile': {
                'vulnerability_score': round(random.random() * 0.3, 2) if random.random() < 0.2 else round(random.random() * 0.1, 2),
                'fraud_history': random.random() < 0.05,
                'kyc_status': 'VERIFIED',
                'pep_status': False
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        customers.append(customer)
        
        # Batch write every 25 items
        if len(customers) >= 25:
            with customers_table.batch_writer() as batch:
                for cust in customers:
                    # Convert floats to Decimal
                    cust_decimal = json.loads(
                        json.dumps(cust, default=decimal_default)
                    )
                    batch.put_item(Item=cust_decimal)
            print(f"  Written {i+1}/{count} customers")
            customers = []
    
    # Write remaining customers
    if customers:
        with customers_table.batch_writer() as batch:
            for cust in customers:
                cust_decimal = json.loads(
                    json.dumps(cust, default=decimal_default)
                )
                batch.put_item(Item=cust_decimal)
    
    print(f"✓ Generated {count} customers")


def generate_transactions(customer_ids, count=10000):
    """Generate realistic transaction history."""
    print(f"Generating {count} transactions...")
    
    transactions = []
    payee_accounts = [fake.bban() for _ in range(500)]  # Pool of payees
    
    for i in range(count):
        transaction_id = f"TXN-{str(uuid.uuid4())[:12].upper()}"
        customer_id = random.choice(customer_ids)
        
        # Generate timestamp within last 180 days
        days_ago = random.randint(0, 180)
        hours_ago = random.randint(0, 23)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        
        # Amount distribution: mostly small, some large
        if random.random() < 0.8:
            amount = round(random.uniform(10, 500), 2)
        elif random.random() < 0.95:
            amount = round(random.uniform(500, 2000), 2)
        else:
            amount = round(random.uniform(2000, 10000), 2)
        
        # Small chance of fraud indicators
        is_fraud = random.random() < 0.03
        risk_score = random.randint(70, 95) if is_fraud else random.randint(0, 60)
        
        transaction = {
            'transaction_id': transaction_id,
            'customer_id': customer_id,
            'timestamp': timestamp.isoformat(),
            'amount': amount,
            'currency': 'GBP',
            'payee_name': fake.company() if not is_fraud else random.choice([
                'Urgent Payment Ltd',
                'Quick Transfer Co',
                'Immediate Solutions'
            ]),
            'payee_account': random.choice(payee_accounts),
            'sort_code': f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}",
            'payment_type': random.choice(['FASTER_PAYMENT', 'BACS', 'CHAPS']),
            'status': random.choice(['COMPLETED', 'PENDING', 'BLOCKED']) if i < count - 100 else 'PENDING',
            'is_fraud': is_fraud,
            'risk_score': risk_score,
            'created_at': timestamp.isoformat(),
            'updated_at': timestamp.isoformat()
        }
        
        transactions.append(transaction)
        
        # Batch write every 25 items
        if len(transactions) >= 25:
            with transactions_table.batch_writer() as batch:
                for txn in transactions:
                    txn_decimal = json.loads(
                        json.dumps(txn, default=decimal_default)
                    )
                    batch.put_item(Item=txn_decimal)
            print(f"  Written {i+1}/{count} transactions")
            transactions = []
    
    # Write remaining transactions
    if transactions:
        with transactions_table.batch_writer() as batch:
            for txn in transactions:
                txn_decimal = json.loads(
                    json.dumps(txn, default=decimal_default)
                )
                batch.put_item(Item=txn_decimal)
    
    print(f"✓ Generated {count} transactions")
    return [t['transaction_id'] for t in transactions if t['is_fraud']]


def generate_cases(customer_ids, transaction_ids, count=100):
    """Generate fraud investigation cases."""
    print(f"Generating {count} cases...")
    
    cases = []
    for i in range(count):
        case_id = f"AEGIS-CASE-{str(i+1).zfill(8)}"
        customer_id = random.choice(customer_ids)
        transaction_id = random.choice(transaction_ids) if transaction_ids and random.random() < 0.5 else f"TXN-{str(uuid.uuid4())[:12].upper()}"
        
        created_date = datetime.now() - timedelta(days=random.randint(0, 60))
        
        # Status distribution
        status_choices = ['Open', 'In Progress', 'Pending Customer', 'Pending Review', 'Resolved - Genuine', 'Resolved - Fraud Blocked']
        status_weights = [0.2, 0.15, 0.1, 0.15, 0.25, 0.15]
        status = random.choices(status_choices, weights=status_weights)[0]
        
        # Priority based on risk score
        risk_score = random.randint(60, 95)
        if risk_score >= 85:
            priority = 'Critical'
        elif risk_score >= 75:
            priority = 'High'
        elif risk_score >= 65:
            priority = 'Medium'
        else:
            priority = 'Low'
        
        reason_codes = random.sample([
            'NEW_PAYEE_HIGH_AMOUNT',
            'VELOCITY_ANOMALY',
            'ACTIVE_CALL_DETECTED',
            'PAYEE_VERIFICATION_MISMATCH',
            'UNUSUAL_BEHAVIORAL_PATTERN',
            'ROUND_AMOUNT',
            'GRAPH_NETWORK_ANOMALY'
        ], k=random.randint(1, 4))
        
        case = {
            'case_id': case_id,
            'customer_id': customer_id,
            'transaction_id': transaction_id,
            'status': status,
            'priority': priority,
            'risk_score': risk_score,
            'confidence': round(random.uniform(0.7, 0.95), 2),
            'reason_codes': reason_codes,
            'created_date': created_date.isoformat(),
            'updated_date': datetime.now().isoformat(),
            'assigned_analyst': f"analyst-{random.randint(1, 5)}" if status in ['In Progress', 'Pending Review'] else None,
            'resolution_date': (created_date + timedelta(days=random.randint(1, 14))).isoformat() if 'Resolved' in status else None
        }
        
        cases.append(case)
        
        # Batch write every 25 items
        if len(cases) >= 25:
            with cases_table.batch_writer() as batch:
                for c in cases:
                    c_decimal = json.loads(
                        json.dumps(c, default=decimal_default)
                    )
                    batch.put_item(Item=c_decimal)
            print(f"  Written {i+1}/{count} cases")
            cases = []
    
    # Write remaining cases
    if cases:
        with cases_table.batch_writer() as batch:
            for c in cases:
                c_decimal = json.loads(
                    json.dumps(c, default=decimal_default)
                )
                batch.put_item(Item=c_decimal)
    
    print(f"✓ Generated {count} cases")


def main():
    """Main execution function."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║     AEGIS - Test Data Population Script                     ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    try:
        # Generate customers first
        generate_customers(count=1000)
        
        # Get customer IDs for transactions and cases
        print("\nRetrieving customer IDs...")
        response = customers_table.scan(ProjectionExpression='customer_id', Limit=1000)
        customer_ids = [item['customer_id'] for item in response['Items']]
        print(f"✓ Retrieved {len(customer_ids)} customer IDs")
        
        # Generate transactions
        print()
        fraud_transaction_ids = generate_transactions(customer_ids, count=10000)
        
        # Generate cases
        print()
        generate_cases(customer_ids, fraud_transaction_ids, count=200)
        
        print()
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║     ✓ Test Data Population Complete                         ║")
        print("║                                                              ║")
        print("║     Summary:                                                ║")
        print(f"║       • Customers: 1,000                                     ║")
        print(f"║       • Transactions: 10,000                                 ║")
        print(f"║       • Cases: 200                                           ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == '__main__':
    main()


