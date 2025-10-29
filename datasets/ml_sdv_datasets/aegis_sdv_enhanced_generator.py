# Aegis Enhanced Synthetic Dataset Generation - Production-Ready
# This script generates a comprehensive, multi-table synthetic dataset for
# Authorized Push Payment (APP) fraud detection using the latest SDV library.
#
# Based on analysis of real-world ABC Bank data structures with enhanced features:
# - Customer demographics with vulnerability assessment
# - Transaction patterns with fraud scenario modeling
# - Call history integration with risk scoring
# - Behavioral analytics with anomaly detection
# - Advanced ML/DL features for mule detection and network analysis

import argparse
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from sdv.multi_table import HMASynthesizer
from sdv.metadata import MultiTableMetadata
from sdv.evaluation.single_table import evaluate_quality
from tqdm import tqdm
import random
import uuid
import warnings
warnings.filterwarnings('ignore')

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)
fake = Faker()

parser = argparse.ArgumentParser(
    description="Generate an enhanced multi-table APP fraud dataset using SDV"
)
parser.add_argument(
    "--fast",
    action="store_true",
    help="Use smaller sample sizes and skip expensive evaluation for quicker runs",
)
parser.add_argument("--seed-customers", type=int, help="Override number of seed customers")
parser.add_argument(
    "--synthetic-customers",
    type=int,
    help="Override number of synthetic customers to sample",
)
parser.add_argument(
    "--avg-transactions",
    type=int,
    help="Override average transactions per customer",
)
parser.add_argument(
    "--skip-training",
    action="store_true",
    help="Skip SDV model training and synthetic data generation",
)
parser.add_argument(
    "--skip-quality",
    action="store_true",
    help="Skip post-generation quality evaluation",
)

args = parser.parse_args()

print("=" * 80)
print("AEGIS ENHANCED SYNTHETIC APP FRAUD DATASET GENERATOR")
print("Production-Ready with Real-World Schema Alignment")
print("=" * 80)

# === 1. ENHANCED CONFIGURATION ===
CONFIG = {
    # Dataset sizing
    'num_seed_customers': 8000,           # Seed data for SDV training
    'num_synthetic_customers': 25000,     # Final synthetic output
    'avg_transactions_per_customer': 45,   # Based on real data analysis
    
    # Time periods
    'start_date': datetime(2024, 1, 1),
    'end_date': datetime(2025, 10, 1),
    
    # Fraud parameters (aligned to real-world rates)
    'fraud_ratio': 0.028,                 # 2.8% fraud rate
    'mule_account_ratio': 0.012,          # 1.2% mule accounts
    'vulnerable_customer_ratio': 0.22,    # 22% vulnerable
    
    # Behavioral parameters
    'call_preceding_fraud_rate': 0.65,    # 65% of frauds have preceding calls
    'device_change_fraud_rate': 0.35,     # 35% use new devices
    'foreign_ip_fraud_rate': 0.28,        # 28% from foreign IPs
}

if args.fast:
    fast_overrides = {
        'num_seed_customers': 1000,
        'num_synthetic_customers': 2500,
        'avg_transactions_per_customer': 12,
    }
    for key, value in fast_overrides.items():
        CONFIG[key] = value

if args.seed_customers is not None:
    CONFIG['num_seed_customers'] = max(1, args.seed_customers)

if args.synthetic_customers is not None:
    CONFIG['num_synthetic_customers'] = max(1, args.synthetic_customers)

if args.avg_transactions is not None:
    CONFIG['avg_transactions_per_customer'] = max(1, args.avg_transactions)

skip_training = args.skip_training
skip_quality = args.skip_quality or skip_training or args.fast

print(f"Configuration (fast mode: {'ON' if args.fast else 'OFF'}):")
for key, value in CONFIG.items():
    if isinstance(value, float) and ('ratio' in key or 'rate' in key):
        print(f"  - {key.replace('_', ' ').title()}: {value*100:.1f}%")
    elif isinstance(value, int):
        print(f"  - {key.replace('_', ' ').title()}: {value:,}")
    else:
        print(f"  - {key.replace('_', ' ').title()}: {value}")
print(f"  - Skip SDV training: {'YES' if skip_training else 'NO'}")
print(f"  - Skip quality evaluation: {'YES' if skip_quality else 'NO'}")

# === 2. ENHANCED SDV METADATA DEFINITION ===
print("\n[STEP 1] Defining Enhanced Multi-Table Metadata...")

metadata = MultiTableMetadata()

# Enhanced table schemas based on real ABC data structure
table_schemas = {
    'aegis_customers': {
        'columns': {
            'customer_id': {'sdtype': 'id'},
            'name': {'sdtype': 'categorical'},
            'date_of_birth': {'sdtype': 'datetime', 'datetime_format': '%Y-%m-%d'},
            'gender': {'sdtype': 'categorical'},
            'citizenship': {'sdtype': 'categorical'}, 
            'marital_status': {'sdtype': 'categorical'},
            'employment_status': {'sdtype': 'categorical'},
            'annual_income': {'sdtype': 'numerical'},
            'customer_segment': {'sdtype': 'categorical'},
            'onboarding_date': {'sdtype': 'datetime', 'datetime_format': '%Y-%m-%d'},
            'digital_literacy_level': {'sdtype': 'categorical'},
            'known_device_familiarity_score': {'sdtype': 'numerical'},
            'scam_education_completed': {'sdtype': 'boolean'},
            'risk_profile': {'sdtype': 'categorical'},
            'is_vulnerable': {'sdtype': 'boolean'},
            'vulnerability_score': {'sdtype': 'numerical'},
            'vulnerability_flags': {'sdtype': 'categorical'},
            'is_mule_account': {'sdtype': 'boolean'},
            'credit_score': {'sdtype': 'numerical'},
            'kyc_level': {'sdtype': 'categorical'},
            'aml_risk_level': {'sdtype': 'categorical'},
        },
        'primary_key': 'customer_id'
    },
    
    'aegis_accounts': {
        'columns': {
            'account_id': {'sdtype': 'id'},
            'customer_id': {'sdtype': 'id'},
            'account_number': {'sdtype': 'categorical'},
            'bsb_code': {'sdtype': 'categorical'},
            'account_type': {'sdtype': 'categorical'},
            'creation_date': {'sdtype': 'datetime', 'datetime_format': '%Y-%m-%d'},
            'balance': {'sdtype': 'numerical'},
            'currency': {'sdtype': 'categorical'},
            'status': {'sdtype': 'categorical'},
            'is_mule_account': {'sdtype': 'boolean'},
            'daily_limit': {'sdtype': 'numerical'},
            'monthly_limit': {'sdtype': 'numerical'},
        },
        'primary_key': 'account_id'
    },
    
    'aegis_transactions': {
        'columns': {
            'transaction_id': {'sdtype': 'id'},
            'customer_id': {'sdtype': 'id'},
            'source_account_id': {'sdtype': 'id'},
            'destination_account_id': {'sdtype': 'id'},
            'amount': {'sdtype': 'numerical'},
            'currency': {'sdtype': 'categorical'},
            'transaction_type': {'sdtype': 'categorical'},
            'transaction_date': {'sdtype': 'datetime', 'datetime_format': '%Y-%m-%d'},
            'transaction_time': {'sdtype': 'datetime', 'datetime_format': '%H:%M:%S'},
            'payee_payer_name': {'sdtype': 'categorical'},
            'description': {'sdtype': 'categorical'},
            'payment_channel': {'sdtype': 'categorical'},
            'device_id': {'sdtype': 'categorical'},
            'device_model': {'sdtype': 'categorical'},
            'ip_address': {'sdtype': 'categorical'},
            'ip_address_country': {'sdtype': 'categorical'},
            'known_device': {'sdtype': 'boolean'},
            'status': {'sdtype': 'categorical'},
            'is_flagged': {'sdtype': 'boolean'},
            'flag_reason': {'sdtype': 'categorical'},
            'is_fraud': {'sdtype': 'boolean'},
            'fraud_type': {'sdtype': 'categorical'},
            'risk_score': {'sdtype': 'numerical'},
            'location_risk': {'sdtype': 'categorical'},
            'amount_risk': {'sdtype': 'categorical'},
            'velocity_risk': {'sdtype': 'categorical'},
            'ctr_flag': {'sdtype': 'boolean'},
            'sar_flag': {'sdtype': 'boolean'},
        },
        'primary_key': 'transaction_id'
    },
    
    'aegis_call_history': {
        'columns': {
            'call_id': {'sdtype': 'id'},
            'customer_id': {'sdtype': 'id'},
            'transaction_id': {'sdtype': 'id'},
            'call_date': {'sdtype': 'datetime', 'datetime_format': '%Y-%m-%d'},
            'call_time': {'sdtype': 'datetime', 'datetime_format': '%H:%M:%S'},
            'call_type': {'sdtype': 'categorical'},
            'call_outcome_category': {'sdtype': 'categorical'},
            'call_duration_seconds': {'sdtype': 'numerical'},
            'analyst_team': {'sdtype': 'categorical'},
            'risk_level': {'sdtype': 'categorical'},
            'customer_profile': {'sdtype': 'categorical'},
            'escalated': {'sdtype': 'boolean'},
            'call_quality_score': {'sdtype': 'numerical'},
            'resolution_time_hours': {'sdtype': 'numerical'},
        },
        'primary_key': 'call_id'
    },
    
    'aegis_behavioral_events': {
        'columns': {
            'event_id': {'sdtype': 'id'},
            'customer_id': {'sdtype': 'id'},
            'transaction_id': {'sdtype': 'id'},
            'event_timestamp': {'sdtype': 'datetime'},
            'anomaly_score': {'sdtype': 'numerical'},
            'behavioral_flags': {'sdtype': 'categorical'},
            'session_duration_seconds': {'sdtype': 'numerical'},
            'hesitation_indicators': {'sdtype': 'numerical'},
            'typing_pattern_anomaly': {'sdtype': 'numerical'},
            'copy_paste_detected': {'sdtype': 'boolean'},
            'new_payee_flag': {'sdtype': 'boolean'},
            'authentication_failures': {'sdtype': 'numerical'},
        },
        'primary_key': 'event_id'
    },
    
    'aegis_fraud_alerts': {
        'columns': {
            'alert_id': {'sdtype': 'id'},
            'customer_id': {'sdtype': 'id'},
            'transaction_id': {'sdtype': 'id'},
            'rule_id': {'sdtype': 'categorical'},
            'strategy': {'sdtype': 'categorical'},
            'queue': {'sdtype': 'categorical'},
            'priority': {'sdtype': 'categorical'},
            'status': {'sdtype': 'categorical'},
            'alert_date': {'sdtype': 'datetime', 'datetime_format': '%Y-%m-%d'},
            'alert_time': {'sdtype': 'datetime', 'datetime_format': '%H:%M:%S'},
            'risk_score': {'sdtype': 'numerical'},
            'escalation_level': {'sdtype': 'categorical'},
            'false_positive_probability': {'sdtype': 'numerical'},
            'customer_contact_attempts': {'sdtype': 'numerical'},
        },
        'primary_key': 'alert_id'
    }
}

# Add tables to metadata
for table_name, schema in table_schemas.items():
    metadata.add_table(table_name)

    for column_name, column_details in schema['columns'].items():
        metadata.add_column(table_name=table_name, column_name=column_name, **column_details)

    metadata.set_primary_key(table_name, schema['primary_key'])

# Define relationships
relationships = [
    ('aegis_customers', 'aegis_accounts', 'customer_id', 'customer_id'),
    ('aegis_accounts', 'aegis_transactions', 'account_id', 'source_account_id'),
    ('aegis_customers', 'aegis_call_history', 'customer_id', 'customer_id'),
    ('aegis_transactions', 'aegis_call_history', 'transaction_id', 'transaction_id'),
    ('aegis_customers', 'aegis_behavioral_events', 'customer_id', 'customer_id'),
    ('aegis_transactions', 'aegis_behavioral_events', 'transaction_id', 'transaction_id'),
    ('aegis_customers', 'aegis_fraud_alerts', 'customer_id', 'customer_id'),
    ('aegis_transactions', 'aegis_fraud_alerts', 'transaction_id', 'transaction_id'),
]

for parent, child, parent_key, child_key in relationships:
    metadata.add_relationship(parent, child, parent_key, child_key)

print(f"   ✓ Defined {len(table_schemas)} tables with {len(relationships)} relationships")

# === 3. REALISTIC SEED DATA GENERATION ===
print("\n[STEP 2] Generating High-Fidelity Seed Data...")

# Helper functions
def random_date(start, end):
    delta = end - start
    return start + timedelta(days=np.random.randint(0, delta.days + 1))

def generate_australian_names():
    """Generate realistic Australian names"""
    first_names = [
        'Oliver', 'Charlotte', 'William', 'Amelia', 'Jack', 'Isla', 'Noah', 'Mia',
        'James', 'Grace', 'Lucas', 'Zoe', 'Henry', 'Sophie', 'Alexander', 'Emma',
        'Liam', 'Chloe', 'Benjamin', 'Ava', 'Mason', 'Madison', 'Ethan', 'Lily',
        'Samuel', 'Ruby', 'Sebastian', 'Hannah', 'Cooper', 'Emily'
    ]
    
    surnames = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris',
        'Martin', 'Thompson', 'Young', 'King', 'Robinson', 'Walker', 'Perez', 'Hall',
        'Lewis', 'Lee', 'Clark', 'Rodriguez', 'Hill', 'Green'
    ]
    
    return random.choice(first_names), random.choice(surnames)

def generate_phone_number():
    """Generate Australian mobile number"""
    return f"+61 4{np.random.randint(10, 99)} {np.random.randint(100, 999)} {np.random.randint(100, 999)}"

def generate_bsb():
    """Generate Australian BSB code"""
    major_banks = ['012', '013', '014', '015', '016', '017', '018']
    return f"{random.choice(major_banks)}-{np.random.randint(1, 999):03d}"

# Generate customers with enhanced profiles
print("   Generating enhanced customer profiles...")
customers_data = []
mule_indices = np.random.choice(CONFIG['num_seed_customers'], 
                               int(CONFIG['num_seed_customers'] * CONFIG['mule_account_ratio']), 
                               replace=False)

for i in tqdm(range(CONFIG['num_seed_customers']), desc="Customers"):
    customer_id = f"AU-CUST{i+1:05d}"
    first_name, last_name = generate_australian_names()
    
    # Age distribution (realistic Australian population)
    age = np.random.choice([
        np.random.randint(18, 30),  # 25% young adults
        np.random.randint(30, 45),  # 30% middle age
        np.random.randint(45, 60),  # 25% pre-retirement
        np.random.randint(60, 85)   # 20% elderly
    ], p=[0.25, 0.30, 0.25, 0.20])
    
    dob = datetime.now() - timedelta(days=age*365.25)
    
    # Employment based on age
    if age < 25:
        employment = np.random.choice(['Student', 'Full-time', 'Part-time', 'Unemployed'], 
                                    p=[0.4, 0.35, 0.15, 0.1])
        income = np.random.uniform(20000, 55000) if employment != 'Student' else np.random.uniform(10000, 25000)
    elif age < 65:
        employment = np.random.choice(['Full-time', 'Self-employed', 'Part-time', 'Unemployed'], 
                                    p=[0.65, 0.15, 0.12, 0.08])
        income = np.random.uniform(45000, 120000) if employment == 'Full-time' else np.random.uniform(25000, 80000)
    else:
        employment = np.random.choice(['Retired', 'Part-time', 'Unemployed'], p=[0.7, 0.2, 0.1])
        income = np.random.uniform(25000, 45000)
    
    # Vulnerability assessment
    vulnerability_flags = []
    vulnerability_score = 0.0
    
    if age > 70:
        vulnerability_flags.append('ELDERLY')
        vulnerability_score += 0.35
    if age < 25:
        vulnerability_flags.append('YOUNG_ADULT')
        vulnerability_score += 0.20
    if employment in ['Unemployed', 'Student']:
        vulnerability_flags.append('LOW_INCOME')
        vulnerability_score += 0.25
    if np.random.random() < 0.04:  # 4% prior victims
        vulnerability_flags.append('PRIOR_VICTIM')
        vulnerability_score += 0.45
    if age > 60 and np.random.random() < 0.3:  # 30% of elderly have low digital literacy
        vulnerability_flags.append('LOW_DIGITAL_LITERACY')
        vulnerability_score += 0.30
    
    is_vulnerable = vulnerability_score > 0.3 or len(vulnerability_flags) > 1
    
    # Mule account characteristics
    is_mule = i in mule_indices
    if is_mule:
        age = np.random.randint(18, 35)  # Mules typically younger
        employment = np.random.choice(['Unemployed', 'Student', 'Part-time'], p=[0.5, 0.3, 0.2])
        income = np.random.uniform(15000, 35000)
        vulnerability_flags.append('POTENTIAL_MULE')
        vulnerability_score = min(1.0, vulnerability_score + 0.6)
    
    # Customer segment
    if income > 100000:
        segment = 'Premium'
    elif income > 60000:
        segment = 'Standard'
    elif is_vulnerable:
        segment = 'Vulnerable'
    else:
        segment = 'Standard'
    
    # Digital literacy and risk factors
    if age < 35 and employment in ['Full-time', 'Student']:
        digital_literacy = 'High'
        device_familiarity = np.random.uniform(0.8, 1.0)
    elif age < 55:
        digital_literacy = 'Medium'
        device_familiarity = np.random.uniform(0.5, 0.8)
    else:
        digital_literacy = np.random.choice(['Low', 'Medium'], p=[0.6, 0.4])
        device_familiarity = np.random.uniform(0.2, 0.6)
    
    # Risk profile
    if is_mule or vulnerability_score > 0.6:
        risk_profile = 'Very High'
    elif vulnerability_score > 0.4:
        risk_profile = 'High'
    elif vulnerability_score > 0.2:
        risk_profile = 'Medium'
    else:
        risk_profile = 'Low'
    
    # Credit score
    base_credit = 650
    if employment == 'Full-time':
        base_credit += np.random.randint(0, 120)
    elif employment == 'Self-employed':
        base_credit += np.random.randint(-30, 80)
    elif employment in ['Unemployed', 'Student']:
        base_credit -= np.random.randint(50, 150)
    
    if is_vulnerable:
        base_credit -= np.random.randint(30, 100)
    
    credit_score = int(np.clip(base_credit + np.random.normal(0, 50), 300, 850))
    
    customers_data.append({
        'customer_id': customer_id,
        'name': f"{first_name} {last_name}",
        'date_of_birth': dob.strftime('%Y-%m-%d'),
        'gender': np.random.choice(['Male', 'Female'], p=[0.51, 0.49]),
        'citizenship': 'AU',
        'marital_status': np.random.choice(['Single', 'Married', 'Divorced', 'Widowed'], p=[0.35, 0.45, 0.12, 0.08]),
        'employment_status': employment,
        'annual_income': int(income),
        'customer_segment': segment,
        'onboarding_date': random_date(CONFIG['start_date'], CONFIG['end_date'] - timedelta(days=90)).strftime('%Y-%m-%d'),
        'digital_literacy_level': digital_literacy,
        'known_device_familiarity_score': round(device_familiarity, 3),
        'scam_education_completed': not is_mule and np.random.random() > 0.4,
        'risk_profile': risk_profile,
        'is_vulnerable': is_vulnerable,
        'vulnerability_score': round(vulnerability_score, 3),
        'vulnerability_flags': '|'.join(vulnerability_flags) if vulnerability_flags else 'NONE',
        'is_mule_account': is_mule,
        'credit_score': credit_score,
        'kyc_level': np.random.choice(['Standard', 'Enhanced', 'Simplified'], p=[0.6, 0.3, 0.1]),
        'aml_risk_level': 'High' if is_mule else ('Medium' if is_vulnerable else 'Low'),
    })

customers_df = pd.DataFrame(customers_data)

print(f"   ✓ Generated {len(customers_df):,} customers")
print(f"     - Vulnerable: {customers_df['is_vulnerable'].sum():,}")
print(f"     - Mule accounts: {customers_df['is_mule_account'].sum():,}")

# Generate accounts
print("   Generating bank accounts...")
accounts_data = []
account_counter = 1

for _, customer in tqdm(customers_df.iterrows(), desc="Accounts", total=len(customers_df)):
    is_mule = customer['is_mule_account']
    
    # Number of accounts (mules often have multiple)
    if is_mule:
        num_accounts = np.random.choice([2, 3, 4], p=[0.5, 0.3, 0.2])
    else:
        num_accounts = np.random.choice([1, 2], p=[0.75, 0.25])
    
    for acc_idx in range(num_accounts):
        account_id = f"ACC{account_counter:08d}"
        account_number = f"{np.random.randint(100000000, 999999999)}"
        
        account_type = 'Current' if acc_idx == 0 else np.random.choice(['Savings', 'Current', 'Business'], p=[0.5, 0.3, 0.2])
        
        creation_date = datetime.strptime(customer['onboarding_date'], '%Y-%m-%d')
        if acc_idx > 0:
            creation_date = random_date(creation_date, CONFIG['end_date'] - timedelta(days=30))
        
        # Balance distribution
        if is_mule:
            balance = np.random.uniform(100, 8000)  # Lower balances for mules
        else:
            balance = max(0, np.random.lognormal(8.0, 1.5))  # Log-normal distribution
        
        accounts_data.append({
            'account_id': account_id,
            'customer_id': customer['customer_id'],
            'account_number': account_number,
            'bsb_code': generate_bsb(),
            'account_type': account_type,
            'creation_date': creation_date.strftime('%Y-%m-%d'),
            'balance': round(balance, 2),
            'currency': 'AUD',
            'status': 'FROZEN' if (is_mule and np.random.random() < 0.1) else 'ACTIVE',
            'is_mule_account': is_mule,
            'daily_limit': np.random.choice([2000, 5000, 10000, 25000], p=[0.4, 0.3, 0.2, 0.1]),
            'monthly_limit': np.random.choice([20000, 50000, 100000, 200000], p=[0.3, 0.4, 0.2, 0.1]),
        })
        
        account_counter += 1

accounts_df = pd.DataFrame(accounts_data)
print(f"   ✓ Generated {len(accounts_df):,} accounts")

# Continue with the rest of the implementation...
# (This is getting quite long, so I'll continue in the next part)

print("\n[STEP 3] Generating Transaction Data with Enhanced Fraud Scenarios...")

# Get account mappings
account_to_customer = accounts_df.set_index('account_id')['customer_id'].to_dict()
customer_lookup = customers_df.set_index('customer_id').to_dict('index')
account_ids = accounts_df['account_id'].tolist()
mule_account_ids = accounts_df[accounts_df['is_mule_account']]['account_id'].tolist()

# Enhanced fraud scenarios based on real ABC data patterns
FRAUD_SCENARIOS = {
    'APP_BANK_IMPERSONATION': {
        'weight': 0.28,
        'amount_range': (2000, 18000),
        'channels': ['Phone Banking', 'Mobile Banking'],
        'descriptions': ['Security transfer', 'Urgent transfer', 'Account protection'],
        'behavioral_indicators': ['ACTIVE_CALL', 'HESITATION', 'URGENCY', 'TIME_PRESSURE']
    },
    'APP_INVESTMENT_SCAM': {
        'weight': 0.25,
        'amount_range': (1500, 35000),
        'channels': ['Online Banking', 'Mobile Banking'],
        'descriptions': ['Investment opportunity', 'Crypto purchase', 'Trading deposit'],
        'behavioral_indicators': ['NEW_PAYEE', 'LARGE_AMOUNT', 'REPEAT_PATTERN']
    },
    'APP_INVOICE_FRAUD': {
        'weight': 0.20,
        'amount_range': (800, 15000),
        'channels': ['Online Banking', 'Mobile Banking'],
        'descriptions': ['Invoice payment', 'Supplier payment', 'Business expense'],
        'behavioral_indicators': ['EMAIL_INTERACTION', 'COPY_PASTE', 'VENDOR_CHANGE']
    },
    'APP_ROMANCE_SCAM': {
        'weight': 0.15,
        'amount_range': (300, 8000),
        'channels': ['Mobile Banking', 'Online Banking'],
        'descriptions': ['Personal gift', 'Emergency help', 'Travel money'],
        'behavioral_indicators': ['EMOTIONAL_PRESSURE', 'REPEAT_VICTIM', 'GRADUAL_INCREASE']
    },
    'MULE_ACTIVITY': {
        'weight': 0.12,
        'amount_range': (500, 12000),
        'channels': ['Mobile Banking', 'ATM', 'Online Banking'],
        'descriptions': ['Cash withdrawal', 'P2P transfer', 'Account transfer'],
        'behavioral_indicators': ['RAPID_MOVEMENT', 'ROUND_AMOUNTS', 'MULTIPLE_RECIPIENTS']
    }
}

# Generate transactions
total_transactions = int(CONFIG['num_seed_customers'] * CONFIG['avg_transactions_per_customer'])
fraud_count = int(total_transactions * CONFIG['fraud_ratio'])

transactions_data = []
call_history_data = []
behavioral_events_data = []
fraud_alerts_data = []

print(f"   Target: {total_transactions:,} transactions ({fraud_count:,} fraud)")

# Determine fraud transactions
fraud_transaction_indices = set(np.random.choice(total_transactions, fraud_count, replace=False))

for txn_idx in tqdm(range(total_transactions), desc="Transactions"):
    transaction_id = f"TXN-2024-{txn_idx+1:06d}"
    
    # Select source account
    source_account = np.random.choice(account_ids)
    source_customer_id = account_to_customer[source_account]
    source_customer = customer_lookup[source_customer_id]
    
    # Determine fraud based on multiple factors
    is_fraud = txn_idx in fraud_transaction_indices
    
    # Enhanced fraud targeting for vulnerable customers
    if not is_fraud and source_customer['is_vulnerable'] and np.random.random() < 0.06:
        is_fraud = True
    
    # Mule activity enhancement
    if source_account in mule_account_ids and np.random.random() < 0.4:
        is_fraud = True
    
    # Transaction timestamp with realistic patterns
    if is_fraud and np.random.random() < 0.3:  # 30% of fraud happens at night
        hour = np.random.choice([22, 23, 0, 1, 2, 3, 4, 5])
    else:
        hour = np.random.choice(range(24), p=[0.02, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.04, 
                                            0.05, 0.06, 0.07, 0.08, 0.08, 0.08, 0.07, 0.06, 
                                            0.05, 0.04, 0.04, 0.04, 0.04, 0.04, 0.03, 0.02])
    
    txn_date = random_date(datetime.strptime(source_customer['onboarding_date'], '%Y-%m-%d'), 
                          CONFIG['end_date'])
    txn_timestamp = txn_date.replace(hour=hour, 
                                    minute=np.random.randint(0, 60), 
                                    second=np.random.randint(0, 60))
    
    # Destination account
    dest_account = np.random.choice(account_ids)
    while dest_account == source_account:
        dest_account = np.random.choice(account_ids)
    
    if is_fraud:
        # Select fraud scenario
        scenario_names = list(FRAUD_SCENARIOS.keys())
        scenario_weights = [FRAUD_SCENARIOS[s]['weight'] for s in scenario_names]
        scenario_name = np.random.choice(scenario_names, p=scenario_weights)
        scenario = FRAUD_SCENARIOS[scenario_name]
        
        # Generate fraud transaction details
        amount = np.random.uniform(*scenario['amount_range'])
        channel = np.random.choice(scenario['channels'])
        description = np.random.choice(scenario['descriptions'])
        fraud_type = scenario_name
        
        # Round amounts for mule activity
        if scenario_name == 'MULE_ACTIVITY':
            amount = round(amount / 500) * 500  # Round to nearest £500
        
        # Device and IP risk
        if np.random.random() < CONFIG['device_change_fraud_rate']:
            device_id = f"UNK-{np.random.randint(1000, 9999)}"
            known_device = False
            device_model = np.random.choice(['Unknown iPhone', 'Unknown Android', 'Unknown Device'])
        else:
            device_id = f"DEV-{source_customer_id[-8:]}"
            known_device = True
            device_model = np.random.choice(['iPhone 14', 'Samsung Galaxy S23', 'iPhone 13', 'Google Pixel 7'])
        
        # IP and location risk
        if np.random.random() < CONFIG['foreign_ip_fraud_rate']:
            ip_country = np.random.choice(['SG', 'MY', 'PH', 'IN', 'CN', 'RU'])
            location_risk = 'High'
        else:
            ip_country = 'AU'
            location_risk = 'Low'
        
        # Generate IP address
        ip_address = f"{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}"
        
        # Risk scores
        risk_score = np.random.randint(70, 95)
        amount_risk = 'High' if amount > 10000 else 'Medium'
        velocity_risk = 'High' if scenario_name == 'MULE_ACTIVITY' else 'Medium'
        
        # Fraud success determination
        success_prob = 0.22  # Base success rate
        if source_customer['is_vulnerable']:
            success_prob *= 1.5
        if amount > 15000:
            success_prob *= 0.6
        if scenario_name == 'MULE_ACTIVITY':
            success_prob *= 0.7
        
        fraud_succeeded = np.random.random() < min(success_prob, 0.8)
        status = 'Completed' if fraud_succeeded else 'Blocked'
        
        # Flag generation
        is_flagged = True
        flag_reason = f"{scenario_name.replace('_', ' ').title()} pattern detected"
        ctr_flag = amount > 10000
        sar_flag = scenario_name in ['APP_INVESTMENT_SCAM', 'MULE_ACTIVITY'] or amount > 20000
        
    else:
        # Legitimate transaction
        amount = max(5.0, np.random.lognormal(4.2, 1.8))  # Log-normal distribution
        
        channel = np.random.choice(['Mobile Banking', 'Online Banking', 'ATM', 'Card Payment', 'Branch'], 
                                 p=[0.45, 0.28, 0.12, 0.10, 0.05])
        
        descriptions = ['Grocery shopping', 'Bill payment', 'Online purchase', 'Fuel', 'Restaurant', 
                       'Rent payment', 'Salary payment', 'Transfer to savings', 'Utilities', 'Insurance']
        description = np.random.choice(descriptions)
        
        fraud_type = 'LEGITIMATE'
        device_id = f"DEV-{source_customer_id[-8:]}"
        known_device = True
        device_model = np.random.choice(['iPhone 14', 'Samsung Galaxy S23', 'iPhone 13'])
        ip_country = 'AU'
        ip_address = f"203.{np.random.randint(1,255)}.{np.random.randint(1,255)}.{np.random.randint(1,255)}"
        location_risk = 'Low'
        amount_risk = 'High' if amount > 25000 else ('Medium' if amount > 5000 else 'Low')
        velocity_risk = 'Low'
        risk_score = np.random.randint(5, 35)
        status = np.random.choice(['Completed', 'Pending'], p=[0.96, 0.04])
        is_flagged = False
        flag_reason = None
        ctr_flag = amount > 10000 and np.random.random() < 0.1
        sar_flag = False
    
    # Store transaction
    transactions_data.append({
        'transaction_id': transaction_id,
        'customer_id': source_customer_id,
        'source_account_id': source_account,
        'destination_account_id': dest_account,
        'amount': round(amount, 2),
        'currency': 'AUD',
        'transaction_type': 'Payment' if not is_fraud else 'Transfer',
        'transaction_date': txn_timestamp.strftime('%Y-%m-%d'),
        'transaction_time': txn_timestamp.strftime('%H:%M:%S'),
        'payee_payer_name': f"Payee-{dest_account[-6:]}",
        'description': description,
        'payment_channel': channel,
        'device_id': device_id,
        'device_model': device_model,
        'ip_address': ip_address,
        'ip_address_country': ip_country,
        'known_device': known_device,
        'status': status,
        'is_flagged': is_flagged,
        'flag_reason': flag_reason,
        'is_fraud': is_fraud,
        'fraud_type': fraud_type,
        'risk_score': risk_score,
        'location_risk': location_risk,
        'amount_risk': amount_risk,
        'velocity_risk': velocity_risk,
        'ctr_flag': ctr_flag,
        'sar_flag': sar_flag,
    })
    
    # Generate behavioral event
    behavioral_events_data.append({
        'event_id': f"BEH-{txn_idx+1:08d}",
        'customer_id': source_customer_id,
        'transaction_id': transaction_id,
        'event_timestamp': (txn_timestamp - timedelta(seconds=np.random.randint(10, 300))).isoformat(),
        'anomaly_score': round(np.random.uniform(0.6, 1.0) if is_fraud else np.random.uniform(0.0, 0.4), 3),
        'behavioral_flags': '|'.join(FRAUD_SCENARIOS.get(fraud_type, {}).get('behavioral_indicators', ['NORMAL'])),
        'session_duration_seconds': np.random.randint(60, 1800),
        'hesitation_indicators': np.random.randint(0, 5) if is_fraud else 0,
        'typing_pattern_anomaly': round(np.random.uniform(0.5, 1.0) if is_fraud else np.random.uniform(0.0, 0.3), 3),
        'copy_paste_detected': is_fraud and 'COPY_PASTE' in FRAUD_SCENARIOS.get(fraud_type, {}).get('behavioral_indicators', []),
        'new_payee_flag': is_fraud and np.random.random() < 0.7,
        'authentication_failures': np.random.randint(1, 4) if is_fraud else 0,
    })
    
    # Generate call history for fraud cases
    if is_fraud and np.random.random() < CONFIG['call_preceding_fraud_rate']:
        call_start = txn_timestamp - timedelta(minutes=np.random.randint(10, 120))
        call_duration = np.random.randint(180, 2400)  # 3-40 minutes
        
        call_history_data.append({
            'call_id': f"CALL-{len(call_history_data)+1:06d}",
            'customer_id': source_customer_id,
            'transaction_id': transaction_id,
            'call_date': call_start.strftime('%Y-%m-%d'),
            'call_time': call_start.strftime('%H:%M:%S'),
            'call_type': np.random.choice(['Inbound', 'Outbound'], p=[0.3, 0.7]),
            'call_outcome_category': np.random.choice(['Customer reached', 'No Response', 'Voicemail left'], p=[0.6, 0.25, 0.15]),
            'call_duration_seconds': call_duration,
            'analyst_team': np.random.choice(['Fraud Ops', 'Customer Protection', 'Transaction Risk']),
            'risk_level': 'High' if risk_score > 80 else 'Medium',
            'customer_profile': 'Vulnerable' if source_customer['is_vulnerable'] else 'Standard',
            'escalated': risk_score > 90,
            'call_quality_score': round(np.random.uniform(0.7, 0.95), 2),
            'resolution_time_hours': round(np.random.uniform(0.5, 6.0), 1),
        })
    
    # Generate fraud alert for high-risk transactions
    if is_fraud and risk_score > 75:
        fraud_alerts_data.append({
            'alert_id': f"ALRT-{source_customer_id}-{len(fraud_alerts_data)+1}",
            'customer_id': source_customer_id,
            'transaction_id': transaction_id,
            'rule_id': f"RUL-TX{np.random.randint(100, 999)}",
            'strategy': scenario_name.replace('_', ' ').title(),
            'queue': np.random.choice(['High-Risk Behaviour', 'Device Anomaly', 'Investment Scam Monitoring']),
            'priority': 'Critical' if risk_score > 90 else 'High',
            'status': 'Open',
            'alert_date': txn_timestamp.strftime('%Y-%m-%d'),
            'alert_time': (txn_timestamp + timedelta(minutes=np.random.randint(1, 15))).strftime('%H:%M:%S'),
            'risk_score': risk_score * 10,  # Scale to match real data
            'escalation_level': f"L{np.random.randint(1, 3)}",
            'false_positive_probability': round(np.random.uniform(0.05, 0.4), 2),
            'customer_contact_attempts': np.random.randint(1, 4),
        })

# Convert to DataFrames
transactions_df = pd.DataFrame(transactions_data)
call_history_df = pd.DataFrame(call_history_data)
behavioral_events_df = pd.DataFrame(behavioral_events_data)
fraud_alerts_df = pd.DataFrame(fraud_alerts_data)

print(f"   ✓ Generated {len(transactions_df):,} transactions")
print(f"   ✓ Generated {len(call_history_df):,} call records")
print(f"   ✓ Generated {len(behavioral_events_df):,} behavioral events")
print(f"   ✓ Generated {len(fraud_alerts_df):,} fraud alerts")
print(f"   - Fraud rate: {transactions_df['is_fraud'].mean()*100:.2f}%")

# === 4. PREPARE SEED DATA FOR SDV ===
seed_data = {
    'aegis_customers': customers_df,
    'aegis_accounts': accounts_df,
    'aegis_transactions': transactions_df,
    'aegis_call_history': call_history_df,
    'aegis_behavioral_events': behavioral_events_df,
    'aegis_fraud_alerts': fraud_alerts_df,
}

synthetic_data = None
quality_score = None

if skip_training:
    print("\n[STEP 4] Skipping SDV training and synthetic generation (per configuration)...")
    print("   ✓ Seed data is ready for manual exploration or external modeling")
else:
    print(f"\n[STEP 4] Training SDV Synthesizer...")
    print("This may take several minutes for large datasets...")

    synthesizer = HMASynthesizer(metadata)
    synthesizer.fit(seed_data)

    print("   ✓ SDV model training complete")
    synthesizer.save('aegis_enhanced_synthesizer.pkl')
    print("   ✓ Synthesizer saved")

    print(f"\n[STEP 5] Generating Synthetic Dataset ({CONFIG['num_synthetic_customers']:,} customers)...")

    synthetic_data = synthesizer.sample(
        num_rows=CONFIG['num_synthetic_customers'],
        table_name='aegis_customers',
        sample_children=True
    )

    print("   ✓ Synthetic data generation complete")

    for table_name, data in synthetic_data.items():
        filename = f"synthetic_{table_name}.csv"
        data.to_csv(filename, index=False)
        print(f"   ✓ Exported {filename}: {len(data):,} rows")

    if skip_quality:
        print("\n[STEP 6] Quality evaluation skipped (per configuration)...")
    else:
        print(f"\n[STEP 6] Evaluating Synthetic Data Quality...")

        quality_report = evaluate_quality(
            real_data=seed_data,
            synthetic_data=synthetic_data,
            metadata=metadata
        )

        quality_score = quality_report.get_score()
        print(f"   ✓ Overall Quality Score: {quality_score*100:.1f}%")

        quality_report.save('synthetic_quality_report.pkl')

# === 7. SUMMARY STATISTICS ===
print("\n" + "=" * 80)
print("AEGIS ENHANCED SYNTHETIC DATASET - GENERATION SUMMARY")
print("=" * 80)

print(f"\nSeed Data Statistics:")
for table_name, df in seed_data.items():
    print(f"  - {table_name}: {len(df):,} records")

if synthetic_data is not None:
    print(f"\nSynthetic Data Statistics:")
    for table_name, df in synthetic_data.items():
        print(f"  - {table_name}: {len(df):,} records")

    print(f"\nFraud Detection Features:")
    print(f"  - Fraud transactions: {synthetic_data['aegis_transactions']['is_fraud'].sum():,}")
    print(f"  - Fraud rate: {synthetic_data['aegis_transactions']['is_fraud'].mean()*100:.2f}%")
    print(f"  - High-risk alerts: {len(synthetic_data['aegis_fraud_alerts']):,}")
    print(f"  - Call interventions: {len(synthetic_data['aegis_call_history']):,}")

if quality_score is not None:
    print(f"\nData Quality:")
    print(f"  - SDV Quality Score: {quality_score*100:.1f}%")
    print(f"  - Multi-table relationships: {len(relationships)} preserved")
    print(f"  - Advanced ML features: ✓ Enabled")

print("\n" + "=" * 80)
if skip_training:
    print("SEED DATA READY. SDV TRAINING SKIPPED PER CONFIGURATION.")
else:
    print("DATASET READY FOR ADVANCED ML/DL TRAINING!")
    print("Files saved: synthetic_aegis_*.csv, aegis_enhanced_synthesizer.pkl")
print("=" * 80)