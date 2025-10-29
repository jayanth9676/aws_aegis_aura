"""
Aegis Dataset Generator
Generates comprehensive fraud prevention datasets aligned with Aegis system architecture
Integrates data from authorized_scams_dataset and expands for production use
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

# Configuration
TOTAL_CUSTOMERS = 100  # Production-ready dataset size
TRANSACTIONS_PER_CUSTOMER_RANGE = (15, 50)  # Realistic transaction volume
FRAUD_RATE = 0.08  # 8% of transactions are fraud (industry realistic)
VULNERABLE_CUSTOMER_RATE = 0.15  # 15% vulnerable customers

# Random seed for reproducibility
random.seed(42)

class AegisDataGenerator:
    def __init__(self):
        self.customers = []
        self.accounts = []
        self.transactions = []
        self.behavioral_events = []
        self.fraud_alerts = []
        self.call_history = []
        self.payees = []
        self.devices = []
        self.graph_relationships = []
        self.cases = []
        self.analyst_pool = []  # Pool of fraud analysts
        
        # Load reference data from authorized_scams_dataset
        self.load_reference_data()
        
    def load_reference_data(self):
        """Load existing data for patterns"""
        datasets_path = os.path.dirname(os.path.abspath(__file__))
        auth_scams_path = os.path.join(os.path.dirname(datasets_path), 'authorized_scams_dataset')
        
        try:
            with open(os.path.join(auth_scams_path, 'customer_demographic.json'), 'r') as f:
                self.ref_customers = json.load(f)['customers']
            with open(os.path.join(auth_scams_path, 'Customer_Transaction_History.json'), 'r') as f:
                self.ref_transactions = json.load(f)['transactions']
            with open(os.path.join(auth_scams_path, 'FTP.json'), 'r') as f:
                self.ref_alerts = json.load(f)['alerts']
            with open(os.path.join(auth_scams_path, 'Enhanced_Customer_Call_History.json'), 'r') as f:
                self.ref_calls = json.load(f)['calls']
        except FileNotFoundError:
            print("Warning: Reference data not found, using synthetic patterns only")
            self.ref_customers = []
            self.ref_transactions = []
            self.ref_alerts = []
            self.ref_calls = []
    
    def generate_customer_id(self, idx: int) -> str:
        return f"AEGIS-CUST-{idx:06d}"
    
    def generate_account_id(self, idx: int) -> str:
        return f"AEGIS-ACC-{idx:06d}"
    
    def generate_transaction_id(self, idx: int) -> str:
        return f"AEGIS-TXN-{idx:08d}"
    
    def generate_alert_id(self, customer_id: str, idx: int) -> str:
        return f"AEGIS-ALRT-{customer_id}-{idx:03d}"
    
    def generate_customer(self, idx: int) -> Dict[str, Any]:
        """Generate a customer record"""
        
        # Use reference data for first 10 customers
        if idx < len(self.ref_customers):
            ref = self.ref_customers[idx]
            base_name = ref['personal_information']['name']
        else:
            # Generate synthetic
            first_names = ["Emma", "Oliver", "Ava", "Noah", "Sophia", "William", "Isabella", "James", "Charlotte", "Benjamin"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
            base_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        name_parts = base_name.split()
        
        # Determine customer segment and risk profile
        segment = random.choices(
            ["Premium", "Standard", "Vulnerable"],
            weights=[0.25, 0.60, 0.15]
        )[0]
        
        is_vulnerable = segment == "Vulnerable" or random.random() < 0.05
        
        # Age distribution affects vulnerability
        if is_vulnerable:
            age = random.choice([random.randint(18, 25), random.randint(65, 85)])
        else:
            age = random.randint(25, 65)
        
        dob = datetime.now() - timedelta(days=age*365 + random.randint(0, 365))
        
        # Digital literacy correlates with age and education
        if age < 35:
            digital_literacy = random.choices(["High", "Medium", "Low"], weights=[0.7, 0.25, 0.05])[0]
        elif age < 55:
            digital_literacy = random.choices(["High", "Medium", "Low"], weights=[0.4, 0.5, 0.1])[0]
        else:
            digital_literacy = random.choices(["High", "Medium", "Low"], weights=[0.2, 0.4, 0.4])[0]
        
        # Risk profile calculation
        risk_factors = []
        if is_vulnerable:
            risk_factors.append("Vulnerable customer")
        if digital_literacy == "Low":
            risk_factors.append("Low digital literacy")
        if age > 70 or age < 25:
            risk_factors.append("Age risk factor")
        
        overall_risk_score = len(risk_factors) * 20 + random.randint(0, 20)
        if overall_risk_score < 30:
            risk_category = "Low"
        elif overall_risk_score < 60:
            risk_category = "Medium"
        else:
            risk_category = "High"
        
        customer_id = self.generate_customer_id(idx + 1)
        
        customer = {
            "customer_id": customer_id,
            "personal_information": {
                "name_first": name_parts[0] if len(name_parts) > 0 else "Unknown",
                "name_middle": name_parts[1] if len(name_parts) > 2 else None,
                "name_last": name_parts[-1] if len(name_parts) > 1 else "Unknown",
                "name_full": base_name,
                "date_of_birth": dob.strftime("%Y-%m-%d"),
                "age": age,
                "gender": random.choice(["Male", "Female", "Non-binary"]),
                "nationality": random.choices(["GB", "US", "AU", "CA", "EU"], weights=[0.5, 0.2, 0.15, 0.1, 0.05])[0],
                "id_verified": random.random() > 0.02,
                "kyc_status": random.choices(["Verified", "Pending", "Expired"], weights=[0.92, 0.05, 0.03])[0],
                "kyc_verification_date": (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime("%Y-%m-%d"),
                "kyc_review_due": (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                "identity_document_type": random.choice(["Passport", "Driver's Licence", "National ID"]),
                "biometric_enrolled": random.random() > 0.3,
                "pep_status": random.random() < 0.01,
                "sanctions_check": "Clear" if random.random() > 0.001 else "Flagged",
                "sanctions_check_date": (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
            },
            "contact_information": {
                "address_line1": f"{random.randint(1, 999)} {random.choice(['High', 'Main', 'Park', 'Church', 'King'])} Street",
                "city": random.choice(["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Liverpool"]),
                "postcode": f"{random.choice(['SW', 'NW', 'SE', 'NE', 'W', 'E'])}{random.randint(1, 20)} {random.randint(1, 9)}{random.choice('ABCDEFGHJKLMNOPRSTUW')}{random.choice('ABCDEFGHJKLMNOPRSTUW')}",
                "country": "GB",
                "email": f"{name_parts[0].lower()}.{name_parts[-1].lower()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com'])}",
                "email_verification_status": "Verified" if random.random() > 0.05 else "Unverified",
                "phone_primary": f"+44 {random.randint(7000000000, 7999999999)}",
                "phone_verification_status": "Verified" if random.random() > 0.03 else "Unverified",
                "preferred_contact_method": random.choices(["Email", "Phone", "SMS", "App"], weights=[0.45, 0.3, 0.15, 0.1])[0],
                "preferred_language": "en-GB"
            },
            "employment": {
                "status": random.choices(["Full-time", "Part-time", "Self-employed", "Retired", "Unemployed", "Student"], 
                                       weights=[0.5, 0.15, 0.15, 0.12, 0.05, 0.03])[0],
                "occupation": random.choice(["Engineer", "Teacher", "Accountant", "Manager", "Consultant", "Retired", "Student"]),
                "annual_income": random.choice([25000, 35000, 45000, 55000, 65000, 75000, 85000, 95000, 110000, 150000]),
                "income_currency": "GBP",
                "employment_verification_status": "Verified" if random.random() > 0.1 else "Pending"
            },
            "customer_details": {
                "customer_since": (datetime.now() - timedelta(days=random.randint(180, 3650))).strftime("%Y-%m-%d"),
                "segment": segment,
                "account_count": random.randint(1, 5),
                "credit_score": random.randint(300, 850),
                "product_holdings": random.sample(["Current Account", "Savings Account", "Credit Card", "Loan", "Mortgage", "Investment Account"], random.randint(1, 4))
            },
            "compliance": {
                "aml_risk_level": random.choices(["Low", "Medium", "High"], weights=[0.75, 0.20, 0.05])[0],
                "cdd_level": random.choices(["Standard", "Enhanced"], weights=[0.85, 0.15])[0],
                "edd_required": random.random() < 0.05,
                "regulatory_reporting_required": random.random() < 0.02,
                "watchlist_status": "Clear" if random.random() > 0.001 else "Flagged",
                "privacy_consent_given": True,
                "marketing_consent_given": random.random() > 0.4
            },
            "behavioral_profile": {
                "digital_literacy_level": digital_literacy,
                "digital_banking_adoption_score": {"High": 0.9, "Medium": 0.6, "Low": 0.3}[digital_literacy],
                "mobile_banking_enabled": random.random() > 0.15,
                "online_banking_enabled": random.random() > 0.05,
                "known_device_count": random.randint(1, 5),
                "known_device_familiarity_score": round(random.uniform(0.5, 1.0), 2),
                "login_frequency_per_week": random.randint(2, 20),
                "preferred_channel": random.choices(["Mobile Banking", "Online Banking", "Branch", "Phone"], 
                                                   weights=[0.5, 0.3, 0.15, 0.05])[0]
            },
            "vulnerability_assessment": {
                "is_vulnerable": is_vulnerable,
                "vulnerability_score": round(random.uniform(0.1, 0.9) if is_vulnerable else random.uniform(0.0, 0.3), 2),
                "vulnerability_flags": risk_factors,
                "scam_education_completed": random.random() > 0.3,
                "prior_fraud_attempts": random.choices([0, 1, 2, 3], weights=[0.85, 0.10, 0.04, 0.01])[0],
                "scam_awareness_score": round(random.uniform(0.3, 1.0), 2)
            },
            "risk_profile": {
                "overall_risk_score": overall_risk_score,
                "risk_category": risk_category,
                "fraud_flag": random.random() < 0.03,
                "fraud_history": [],
                "last_risk_assessment": (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d"),
                "next_risk_assessment": (datetime.now() + timedelta(days=random.randint(90, 365))).strftime("%Y-%m-%d"),
                "risk_factors": risk_factors
            }
        }
        
        return customer
    
    def generate_account(self, customer_id: str, idx: int, is_primary: bool = False) -> Dict[str, Any]:
        """Generate an account record"""
        account_types = ["Current Account", "Savings Account", "Credit Card", "Business Account", "Premium Account"]
        
        account = {
            "account_id": self.generate_account_id(idx),
            "customer_id": customer_id,
            "account_number": f"{random.randint(10000000, 99999999):08d}",
            "sort_code": f"{random.randint(10, 99):02d}-{random.randint(10, 99):02d}-{random.randint(10, 99):02d}",
            "account_type": account_types[0] if is_primary else random.choice(account_types),
            "creation_date": (datetime.now() - timedelta(days=random.randint(180, 3650))).strftime("%Y-%m-%d"),
            "balance": round(random.uniform(100, 50000), 2),
            "currency": "GBP",
            "status": random.choices(["Active", "Dormant", "Frozen"], weights=[0.92, 0.05, 0.03])[0],
            "is_mule_account": random.random() < 0.02,
            "daily_limit": random.choice([1000, 2000, 5000, 10000, 25000]),
            "monthly_limit": random.choice([10000, 25000, 50000, 100000])
        }
        
        return account
    
    def generate_transaction(self, customer_id: str, account_id: str, idx: int, 
                            is_fraud: bool = False, fraud_type: str = None) -> Dict[str, Any]:
        """Generate a transaction record"""
        
        # Transaction types and categories
        if is_fraud:
            transaction_types = ["Transfer", "Payment"]
            categories = random.choices(
                ["Cryptocurrency", "Investment", "Unknown", "Gambling", "Offshore Transfer"],
                weights=[0.3, 0.3, 0.2, 0.1, 0.1]
            )[0]
            amount_range = (1000, 50000)
            known_device = random.random() < 0.3  # Fraudulent often from unknown devices
        else:
            transaction_types = ["Payment", "Transfer", "Deposit", "Withdrawal"]
            categories = random.choice(["Groceries", "Utilities", "Transport", "Entertainment", 
                                       "Shopping", "Dining", "Healthcare", "Transfer"])
            amount_range = (10, 2000)
            known_device = random.random() < 0.95  # Legitimate usually from known devices
        
        transaction_date = datetime.now() - timedelta(days=random.randint(0, 90))
        
        # Fraud patterns
        if is_fraud:
            # Unusual hours for fraud
            hour = random.choices(range(24), weights=[2]*6 + [1]*12 + [2]*6)[0]
            risk_score = random.randint(70, 99)
            location_risk = random.choices(["Low", "Medium", "High"], weights=[0.2, 0.3, 0.5])[0]
            amount_risk = random.choices(["Low", "Medium", "High"], weights=[0.1, 0.3, 0.6])[0]
            velocity_risk = random.choices(["Low", "Medium", "High"], weights=[0.1, 0.3, 0.6])[0]
        else:
            # Normal business hours for legitimate
            hour = random.choices(range(24), weights=[1]*8 + [5]*12 + [1]*4)[0]
            risk_score = random.randint(0, 40)
            location_risk = "Low"
            amount_risk = "Low"
            velocity_risk = "Low"
        
        transaction_time = f"{hour:02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
        amount = round(random.uniform(*amount_range), 2)
        
        transaction = {
            "transaction_id": self.generate_transaction_id(idx),
            "customer_id": customer_id,
            "account_id": account_id,
            "amount": amount,
            "currency": "GBP",
            "transaction_type": random.choice(transaction_types),
            "transaction_date": transaction_date.strftime("%Y-%m-%d"),
            "transaction_time": transaction_time,
            "timestamp": f"{transaction_date.strftime('%Y-%m-%d')}T{transaction_time}Z",
            "payee_payer_name": random.choice([
                "Tesco", "Sainsbury's", "Amazon", "PayPal", "Utilities Co", "Transport Service",
                "Unknown Recipient", "Crypto Exchange", "Investment Platform", "Online Casino"
            ]) if not is_fraud else random.choice([
                "Unknown Recipient", "Crypto Exchange", "Investment Platform", "Offshore Entity"
            ]),
            "description": categories,
            "payment_channel": random.choices(
                ["Mobile Banking", "Online Banking", "Branch", "ATM", "POS"],
                weights=[0.45, 0.30, 0.10, 0.10, 0.05]
            )[0],
            "device_id": f"DEV-{random.randint(1, 20):04d}",
            "device_model": random.choice(["iPhone 14", "Samsung Galaxy S23", "Google Pixel 8", "Unknown"]),
            "device_os": random.choice(["iOS 17", "Android 14", "Unknown"]),
            "device_fingerprint": uuid.uuid4().hex[:16],
            "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "ip_country": random.choices(
                ["GB", "US", "SG", "MT", "LV", "CY"],
                weights=[0.7, 0.1, 0.05, 0.05, 0.05, 0.05] if not is_fraud else [0.3, 0.2, 0.2, 0.1, 0.1, 0.1]
            )[0],
            "known_device": known_device,
            "status": random.choices(["Completed", "Pending", "Blocked"], 
                                    weights=[0.85, 0.10, 0.05] if not is_fraud else [0.4, 0.4, 0.2])[0],
            "is_flagged": is_fraud or random.random() < 0.05,
            "flag_reason": fraud_type if is_fraud else None,
            "is_fraud": is_fraud,
            "fraud_type": fraud_type if is_fraud else None,
            "risk_score": risk_score,
            "location_risk": location_risk,
            "amount_risk": amount_risk,
            "velocity_risk": velocity_risk,
            "ml_fraud_probability": round(random.uniform(0.7, 0.99), 2) if is_fraud else round(random.uniform(0.0, 0.3), 2),
            "ctr_flag": amount >= 10000,
            "sar_flag": is_fraud and random.random() < 0.5
        }
        
        return transaction
    
    def generate_behavioral_event(self, customer_id: str, transaction_id: str, idx: int) -> Dict[str, Any]:
        """Generate behavioral event data"""
        
        event = {
            "event_id": f"AEGIS-BEH-{idx:08d}",
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "event_timestamp": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
            "session_id": f"SESSION-{uuid.uuid4().hex[:12]}",
            "session_duration_seconds": random.randint(30, 600),
            "page_views": random.randint(2, 15),
            "mouse_movements": random.randint(50, 500),
            "keyboard_events": random.randint(20, 200),
            "anomaly_score": round(random.uniform(0.0, 1.0), 2),
            "behavioral_flags": random.sample([
                "hesitation_detected", "copy_paste_detected", "new_payee", 
                "unusual_hours", "rapid_navigation", "authentication_failures"
            ], random.randint(0, 3)),
            "hesitation_indicators": random.randint(0, 5),
            "typing_pattern_anomaly": round(random.uniform(0.0, 1.0), 2),
            "copy_paste_detected": random.random() < 0.3,
            "new_payee_flag": random.random() < 0.2,
            "authentication_failures": random.randint(0, 3),
            "location_change_detected": random.random() < 0.1,
            "device_change_detected": random.random() < 0.15
        }
        
        return event
    
    def generate_fraud_alert(self, customer_id: str, transaction_id: str, idx: int) -> Dict[str, Any]:
        """Generate fraud alert"""
        
        strategies = [
            "Large Fund Transfer Post Password Change",
            "Business Invoice Redirection",
            "New Device + Account Cleanout",
            "Drip Transfer Anomaly",
            "Investment Scam First-Time Pattern",
            "Full Balance Outflow Detection",
            "Unusual Gambling Activity",
            "Offshore Investment Unusual Pattern",
            "Cryptocurrency Rapid Conversion",
            "Romance Scam Pattern"
        ]
        
        rule_ids = [
            "RUL-TX901", "RUL-TX230", "RUL-TX817", "RUL-TX155",
            "RUL-TX488", "RUL-TX778", "RUL-TX124", "RUL-TX234",
            "RUL-CRY101", "RUL-RS001"
        ]
        
        strategy = random.choice(strategies)
        rule_id = random.choice(rule_ids)
        risk_score = random.randint(600, 1000)
        
        alert = {
            "alert_id": self.generate_alert_id(customer_id, idx),
            "customer_id": customer_id,
            "transaction_id": transaction_id,
            "rule_id": rule_id,
            "strategy": strategy,
            "queue": random.choice([
                "High-Risk Behaviour Queue",
                "Commercial Fraud Queue",
                "Device Anomaly Queue",
                "Investment Scam Monitoring",
                "Behavioural Anomaly Queue"
            ]),
            "priority": random.choices(["Low", "Medium", "High", "Critical"], weights=[0.1, 0.2, 0.5, 0.2])[0],
            "status": random.choices(["Open", "In Progress", "Resolved", "False Positive"], 
                                    weights=[0.3, 0.3, 0.3, 0.1])[0],
            "description": f"{strategy} detected - automated alert",
            "alert_date": (datetime.now() - timedelta(days=random.randint(0, 90))).strftime("%Y-%m-%d"),
            "alert_time": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
            "risk_score": risk_score,
            "escalation_level": "L3" if risk_score > 900 else "L2" if risk_score > 750 else "L1",
            "regulatory_alert_type": random.choice([
                "Suspicious Transaction", "Investment Scam", "Account Takeover",
                "Business Email Compromise", "Problem Gambling"
            ]),
            "compliance_flags": random.sample(["CTR", "SAR", "STR"], random.randint(0, 2)),
            "investigation_status": random.choice(["Pending", "In Progress", "Completed", "Escalated"]),
            "false_positive_probability": round(random.uniform(0.0, 0.5), 2),
            "customer_contact_attempts": random.randint(0, 5),
            "ml_confidence_score": round(random.uniform(0.6, 0.99), 2),
            "shap_explanation": {
                "top_features": [
                    {"feature": "transaction_amount", "contribution": round(random.uniform(0.1, 0.4), 2)},
                    {"feature": "device_risk", "contribution": round(random.uniform(0.1, 0.3), 2)},
                    {"feature": "location_anomaly", "contribution": round(random.uniform(0.05, 0.2), 2)}
                ]
            }
        }
        
        return alert
    
    def generate_device(self, customer_id: str, idx: int) -> Dict[str, Any]:
        """Generate device information"""
        
        device = {
            "device_id": f"AEGIS-DEV-{idx:06d}",
            "customer_id": customer_id,
            "device_fingerprint": uuid.uuid4().hex[:16],
            "device_type": random.choice(["Mobile", "Desktop", "Tablet"]),
            "device_model": random.choice(["iPhone 14", "Samsung Galaxy S23", "MacBook Pro", "Windows PC", "iPad Air"]),
            "device_os": random.choice(["iOS 17", "Android 14", "macOS 14", "Windows 11", "iPadOS 17"]),
            "browser": random.choice(["Safari", "Chrome", "Firefox", "Edge"]),
            "is_trusted": random.random() < 0.85,
            "trust_score": round(random.uniform(0.5, 1.0), 2),
            "first_seen": (datetime.now() - timedelta(days=random.randint(30, 1000))).strftime("%Y-%m-%d"),
            "last_seen": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "location_history": random.sample(["London", "Manchester", "Birmingham", "Glasgow"], random.randint(1, 3)),
            "biometric_enabled": random.random() < 0.7
        }
        
        return device
    
    def generate_payee(self, idx: int) -> Dict[str, Any]:
        """Generate payee/merchant information"""
        
        payee_types = ["Individual", "Business", "Cryptocurrency Exchange", "Investment Platform", "Merchant"]
        
        payee = {
            "payee_id": f"AEGIS-PAYEE-{idx:06d}",
            "payee_name": random.choice([
                "John Smith", "Crypto Exchange Ltd", "Global Investment Partners",
                "Tesco PLC", "Amazon UK", "Unknown Recipient", "PayPal Inc"
            ]),
            "payee_type": random.choice(payee_types),
            "account_number": f"{random.randint(10000000, 99999999):08d}",
            "sort_code": f"{random.randint(10, 99):02d}-{random.randint(10, 99):02d}-{random.randint(10, 99):02d}",
            "registration_number": f"REG{random.randint(100000, 999999)}" if random.random() < 0.7 else None,
            "watchlist_status": random.choices(["Clear", "Flagged", "Blocked"], weights=[0.9, 0.08, 0.02])[0],
            "cop_verified": random.random() < 0.7,
            "sanctions_check": random.choices(["Clear", "Flagged"], weights=[0.98, 0.02])[0],
            "fraud_reports_count": random.choices([0, 1, 2, 3, 4, 5], weights=[0.85, 0.08, 0.04, 0.02, 0.005, 0.005])[0],
            "first_transaction_date": (datetime.now() - timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d"),
            "total_transaction_count": random.randint(1, 100),
            "average_transaction_amount": round(random.uniform(100, 5000), 2),
            "risk_score": random.randint(0, 100)
        }
        
        return payee
    
    def generate_analyst(self, idx: int) -> Dict[str, Any]:
        """Generate fraud analyst profile"""
        first_names = ["Sarah", "Michael", "Emma", "James", "Olivia", "Robert", "Sophia", "William", "Ava", "David"]
        last_names = ["Mitchell", "Rodriguez", "Thompson", "Wilson", "Anderson", "Taylor", "Brown", "Davies", "Evans", "Thomas"]
        
        analyst = {
            "analyst_id": f"AEGIS-ANALYST-{idx:03d}",
            "name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "team": random.choice([
                "Fraud Ops East", "Fraud Ops West", "Device Trust Unit",
                "Transaction Risk", "Customer Protection", "Investment Risk",
                "Behavioral Risk", "Commercial Fraud", "Crypto Risk"
            ]),
            "level": random.choices(["Trainee", "Analyst", "Senior", "Specialist", "Lead"], 
                                   weights=[0.15, 0.35, 0.25, 0.20, 0.05])[0],
            "expertise": random.sample([
                "APP Scams", "Investment Fraud", "Romance Scams", "Business Email Compromise",
                "Account Takeover", "Cryptocurrency Fraud", "Mule Accounts"
            ], random.randint(2, 4)),
            "average_case_resolution_hours": round(random.uniform(1.0, 8.0), 1),
            "case_success_rate": round(random.uniform(0.75, 0.98), 2),
            "total_cases_handled": random.randint(50, 500)
        }
        
        return analyst
    
    def generate_call_record(self, alert: Dict[str, Any], customer_id: str, idx: int) -> Dict[str, Any]:
        """Generate call history record for an alert"""
        
        if not self.analyst_pool:
            # Generate analyst pool if not exists
            for i in range(20):
                self.analyst_pool.append(self.generate_analyst(i + 1))
        
        analyst = random.choice(self.analyst_pool)
        
        call = {
            "call_id": f"AEGIS-CALL-{idx:08d}",
            "customer_id": customer_id,
            "alert_id": alert['alert_id'],
            "transaction_id": alert['transaction_id'],
            "call_date": alert['alert_date'],
            "call_time": f"{random.randint(8, 20):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
            "analyst_id": analyst['analyst_id'],
            "analyst_name": analyst['name'],
            "analyst_team": analyst['team'],
            "analyst_level": analyst['level'],
            "call_type": random.choices(["Inbound", "Outbound"], weights=[0.3, 0.7])[0],
            "call_outcome_category": random.choices([
                "Customer reached", "No Response", "Voicemail left", "Disconnected"
            ], weights=[0.5, 0.2, 0.2, 0.1])[0],
            "follow_up_required": random.random() < 0.4,
            "next_action": random.choice(["Monitor", "Follow up", "Intervention required", "Educate", "Escalate"]),
            "memo": f"Alert {alert['strategy']} - Investigation and customer contact",
            "channel": random.choice(["Phone", "Mobile App", "Internet Banking", "Email"]),
            "call_duration_seconds": random.randint(60, 900),
            "language": "en-GB",
            "risk_level": alert.get('priority', 'Medium'),
            "escalated": alert['escalation_level'] in ['L2', 'L3'] or random.random() < 0.1,
            "call_quality_score": round(random.uniform(0.75, 0.98), 2),
            "recording_available": random.random() < 0.95,
            "regulatory_reporting_required": "SAR" in alert.get('compliance_flags', []),
            "resolution_time_hours": round(random.uniform(0.5, 12.0), 1),
            "customer_satisfaction_score": round(random.uniform(3.0, 5.0), 1) if random.random() < 0.7 else None
        }
        
        return call
    
    def generate_case(self, alert: Dict[str, Any], customer_id: str, idx: int) -> Dict[str, Any]:
        """Generate case management record for Investigation Agent"""
        
        if not self.analyst_pool:
            for i in range(20):
                self.analyst_pool.append(self.generate_analyst(i + 1))
        
        assigned_analyst = random.choice(self.analyst_pool)
        
        case_status = random.choices([
            "Open", "In Progress", "Pending Customer", "Pending Review",
            "Resolved - Fraud Confirmed", "Resolved - False Positive", "Closed"
        ], weights=[0.15, 0.25, 0.15, 0.10, 0.15, 0.10, 0.10])[0]
        
        case = {
            "case_id": f"AEGIS-CASE-{idx:08d}",
            "alert_id": alert['alert_id'],
            "customer_id": customer_id,
            "transaction_id": alert['transaction_id'],
            "case_type": alert['strategy'],
            "priority": alert['priority'],
            "status": case_status,
            "created_date": alert['alert_date'],
            "created_time": alert['alert_time'],
            "assigned_analyst_id": assigned_analyst['analyst_id'],
            "assigned_analyst_name": assigned_analyst['name'],
            "assigned_team": assigned_analyst['team'],
            "sla_deadline": (datetime.strptime(alert['alert_date'], "%Y-%m-%d") + 
                           timedelta(hours=24 if alert['priority'] == 'Critical' else 
                                   48 if alert['priority'] == 'High' else 72)).strftime("%Y-%m-%d %H:%M:%S"),
            "investigation_summary": f"Investigating {alert['strategy']} pattern. Risk score: {alert['risk_score']}",
            "evidence_collected": random.sample([
                "Transaction logs", "Device fingerprints", "IP geolocation",
                "Customer call recording", "Behavioral biometrics", "Email communications",
                "Payee verification", "Similar pattern analysis"
            ], random.randint(3, 6)),
            "customer_contacted": random.random() < 0.8,
            "customer_response": random.choice([
                "Confirmed legitimate", "Denied authorization", "No response",
                "Confirmed fraud", "Partially confirmed"
            ]) if random.random() < 0.7 else None,
            "fraud_confirmed": "Fraud Confirmed" in case_status,
            "loss_amount": alert.get('amount', 0) if "Fraud Confirmed" in case_status else 0,
            "recovery_amount": 0,
            "escalated_to_law_enforcement": random.random() < 0.05 and "Fraud Confirmed" in case_status,
            "sar_filed": "SAR" in alert.get('compliance_flags', []),
            "resolution_time_hours": round(random.uniform(0.5, 48.0), 1) if "Resolved" in case_status or case_status == "Closed" else None,
            "notes": [
                {
                    "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                    "analyst": assigned_analyst['name'],
                    "note": f"Case investigation started. Alert triggered by {alert['rule_id']}"
                }
            ],
            "ai_copilot_recommendations": [
                {
                    "recommendation_type": "Similar Cases",
                    "confidence": round(random.uniform(0.7, 0.95), 2),
                    "details": f"Found {random.randint(3, 15)} similar patterns in historical data"
                },
                {
                    "recommendation_type": "Risk Assessment",
                    "confidence": round(random.uniform(0.6, 0.90), 2),
                    "details": f"ML model fraud probability: {alert.get('ml_confidence_score', 0.8)}"
                }
            ]
        }
        
        return case
    
    def generate_graph_relationship(self, idx: int) -> Dict[str, Any]:
        """Generate graph relationship for Neptune database"""
        
        relationship_types = [
            "TRANSACTS_WITH", "SHARES_DEVICE", "SHARES_IP",
            "SAME_PAYEE", "SIMILAR_PATTERN", "MONEY_FLOW",
            "LINKED_ACCOUNT", "FAMILY_MEMBER"
        ]
        
        # Create relationships between random entities
        if len(self.customers) < 2:
            return None
        
        source_customer = random.choice(self.customers)
        target_customer = random.choice(self.customers)
        
        relationship = {
            "relationship_id": f"AEGIS-REL-{idx:08d}",
            "relationship_type": random.choice(relationship_types),
            "source_entity_type": "Customer",
            "source_entity_id": source_customer['customer_id'],
            "target_entity_type": random.choice(["Customer", "Payee", "Device"]),
            "target_entity_id": target_customer['customer_id'],  # Simplified for now
            "relationship_strength": round(random.uniform(0.1, 1.0), 2),
            "first_detected": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "last_updated": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "transaction_count": random.randint(1, 50),
            "total_amount": round(random.uniform(100, 50000), 2),
            "risk_indicator": random.random() < 0.15,
            "metadata": {
                "shared_attributes": random.sample([
                    "IP Address", "Device Fingerprint", "Payee", "Timing Pattern"
                ], random.randint(1, 3))
            }
        }
        
        return relationship
    
    def generate_all_data(self):
        """Generate all datasets"""
        print("Generating Aegis datasets...")
        
        # Generate customers
        print(f"Generating {TOTAL_CUSTOMERS} customers...")
        for i in range(TOTAL_CUSTOMERS):
            customer = self.generate_customer(i)
            self.customers.append(customer)
            
            # Generate accounts for each customer
            account_count = customer['customer_details']['account_count']
            for j in range(account_count):
                account = self.generate_account(customer['customer_id'], len(self.accounts) + 1, is_primary=(j == 0))
                self.accounts.append(account)
            
            # Generate devices for each customer
            device_count = customer['behavioral_profile']['known_device_count']
            for j in range(device_count):
                device = self.generate_device(customer['customer_id'], len(self.devices) + 1)
                self.devices.append(device)
        
        print(f"Generated {len(self.customers)} customers, {len(self.accounts)} accounts, {len(self.devices)} devices")
        
        # Generate transactions
        print("Generating transactions...")
        for customer in self.customers:
            customer_accounts = [acc for acc in self.accounts if acc['customer_id'] == customer['customer_id']]
            if not customer_accounts:
                continue
            
            num_transactions = random.randint(*TRANSACTIONS_PER_CUSTOMER_RANGE)
            fraud_count = int(num_transactions * FRAUD_RATE)
            
            for i in range(num_transactions):
                account = random.choice(customer_accounts)
                is_fraud = i < fraud_count
                fraud_type = random.choice([
                    "APP Scam", "Investment Scam", "Romance Scam", "Crypto Scam",
                    "Invoice Fraud", "Account Takeover", "Mule Account"
                ]) if is_fraud else None
                
                transaction = self.generate_transaction(
                    customer['customer_id'],
                    account['account_id'],
                    len(self.transactions) + 1,
                    is_fraud=is_fraud,
                    fraud_type=fraud_type
                )
                self.transactions.append(transaction)
                
                # Generate behavioral event for each transaction
                behavioral_event = self.generate_behavioral_event(
                    customer['customer_id'],
                    transaction['transaction_id'],
                    len(self.behavioral_events) + 1
                )
                self.behavioral_events.append(behavioral_event)
                
                # Generate alert for flagged transactions
                if transaction['is_flagged']:
                    alert = self.generate_fraud_alert(
                        customer['customer_id'],
                        transaction['transaction_id'],
                        len(self.fraud_alerts) + 1
                    )
                    self.fraud_alerts.append(alert)
        
        print(f"Generated {len(self.transactions)} transactions, {len(self.behavioral_events)} behavioral events, {len(self.fraud_alerts)} fraud alerts")
        
        # Generate payees
        print("Generating payees...")
        unique_payees = set([txn['payee_payer_name'] for txn in self.transactions])
        for idx, payee_name in enumerate(unique_payees, 1):
            payee = self.generate_payee(idx)
            payee['payee_name'] = payee_name
            self.payees.append(payee)
        
        # Generate call history for alerts (about 70% of alerts get calls)
        print("Generating call history...")
        for alert in self.fraud_alerts:
            if random.random() < 0.7:  # 70% of alerts get customer contact
                # Sometimes multiple calls per alert
                num_calls = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
                for i in range(num_calls):
                    call = self.generate_call_record(alert, alert['customer_id'], len(self.call_history) + 1)
                    self.call_history.append(call)
        
        print(f"Generated {len(self.call_history)} call records")
        
        # Generate cases for all high-priority alerts
        print("Generating case management records...")
        for alert in self.fraud_alerts:
            if alert['priority'] in ['High', 'Critical'] or random.random() < 0.5:
                case = self.generate_case(alert, alert['customer_id'], len(self.cases) + 1)
                self.cases.append(case)
        
        print(f"Generated {len(self.cases)} case records")
        
        # Generate graph relationships
        print("Generating graph relationships for Neptune...")
        num_relationships = min(500, len(self.customers) * 5)  # 5 relationships per customer on average
        for i in range(num_relationships):
            relationship = self.generate_graph_relationship(i + 1)
            if relationship:
                self.graph_relationships.append(relationship)
        
        print(f"Generated {len(self.graph_relationships)} graph relationships")
        
    def save_datasets(self):
        """Save all datasets to JSON files"""
        output_dir = os.path.dirname(os.path.abspath(__file__))
        
        datasets = {
            "aegis_customers.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Customer Master Data",
                    "total_records": len(self.customers),
                    "data_owner": "Aegis Fraud Operations",
                    "classification_level": "Confidential",
                    "compliance_standards": ["KYC", "AML", "CDD", "GDPR", "PSR"],
                    "system_compatibility": ["AgentCore Runtime", "Neptune Graph DB", "DynamoDB"]
                },
                "customers": self.customers
            },
            "aegis_accounts.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Account Master Data",
                    "total_records": len(self.accounts),
                    "system_compatibility": ["DynamoDB", "Account Service API"]
                },
                "accounts": self.accounts
            },
            "aegis_transactions.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Transaction Data with ML Features",
                    "total_records": len(self.transactions),
                    "fraud_rate": f"{(sum(1 for t in self.transactions if t['is_fraud']) / len(self.transactions) * 100):.2f}%",
                    "system_compatibility": ["Transaction Context Agent", "ML Model Service", "DynamoDB"]
                },
                "transactions": self.transactions
            },
            "aegis_behavioral_events.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Behavioral Biometrics Data",
                    "total_records": len(self.behavioral_events),
                    "system_compatibility": ["Behavioral Analysis Agent", "Session Storage", "DynamoDB"]
                },
                "behavioral_events": self.behavioral_events
            },
            "aegis_fraud_alerts.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Fraud Alerts with SHAP Explanations",
                    "total_records": len(self.fraud_alerts),
                    "system_compatibility": ["Supervisor Agent", "Triage Agent", "Investigation Agent", "DynamoDB"]
                },
                "fraud_alerts": self.fraud_alerts
            },
            "aegis_devices.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Device Trust Data",
                    "total_records": len(self.devices),
                    "system_compatibility": ["Device Trust Service", "Redis Session Store"]
                },
                "devices": self.devices
            },
            "aegis_payees.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Payee/Merchant Data for CoP Verification",
                    "total_records": len(self.payees),
                    "system_compatibility": ["Payee Context Agent", "CoP Verification Tool", "Watchlist Service"]
                },
                "payees": self.payees
            },
            "aegis_call_history.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Call History with Analyst Data",
                    "total_records": len(self.call_history),
                    "system_compatibility": ["Dialogue Agent", "Investigation Agent", "DynamoDB"]
                },
                "call_history": self.call_history
            },
            "aegis_cases.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Case Management for Investigation Agent",
                    "total_records": len(self.cases),
                    "system_compatibility": ["Investigation Agent", "AI Copilot", "Case Management UI", "DynamoDB"]
                },
                "cases": self.cases
            },
            "aegis_graph_relationships.json": {
                "metadata": {
                    "version": "4.0",
                    "created_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": "Aegis Fraud Prevention Platform - Graph Relationships for Neptune",
                    "total_records": len(self.graph_relationships),
                    "system_compatibility": ["Graph Relationship Agent", "Neptune Graph DB", "Pattern Detection"]
                },
                "relationships": self.graph_relationships
            }
        }
        
        for filename, data in datasets.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved {filepath}")
            
        # Print summary statistics
        print("\n" + "=" * 60)
        print(" " * 15 + "Dataset Generation Summary")
        print("=" * 60)
        print(f"Total Customers:          {len(self.customers):>8}")
        print(f"Total Accounts:           {len(self.accounts):>8}")
        print(f"Total Devices:            {len(self.devices):>8}")
        print(f"Total Payees:             {len(self.payees):>8}")
        print("-" * 60)
        print(f"Total Transactions:       {len(self.transactions):>8}")
        print(f"  - Fraudulent:           {sum(1 for t in self.transactions if t['is_fraud']):>8}")
        print(f"  - Legitimate:           {sum(1 for t in self.transactions if not t['is_fraud']):>8}")
        print(f"  - Fraud Rate:           {(sum(1 for t in self.transactions if t['is_fraud']) / len(self.transactions) * 100):>7.2f}%")
        print("-" * 60)
        print(f"Total Behavioral Events:  {len(self.behavioral_events):>8}")
        print(f"Total Fraud Alerts:       {len(self.fraud_alerts):>8}")
        print(f"Total Call Records:       {len(self.call_history):>8}")
        print(f"Total Cases:              {len(self.cases):>8}")
        print(f"Total Graph Relationships:{len(self.graph_relationships):>8}")
        print("=" * 60)
        print("\n✓ All datasets generated successfully!")

if __name__ == "__main__":
    generator = AegisDataGenerator()
    generator.generate_all_data()
    generator.save_datasets()
    print("Dataset generation complete!")

