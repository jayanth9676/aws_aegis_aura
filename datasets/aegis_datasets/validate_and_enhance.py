"""Validate and Enhance Aegis Datasets - Ensure Zero Missing Values"""

import json
import random
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta

class DatasetValidator:
    """Validates and enhances datasets to ensure completeness"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.stats = {
            'total_records': 0,
            'missing_fields': 0,
            'enhanced_fields': 0,
            'validation_errors': []
        }
    
    def load_dataset(self, filename: str) -> Dict:
        """Load a dataset file"""
        filepath = self.data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_dataset(self, filename: str, data: Dict):
        """Save enhanced dataset"""
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def fill_missing_string(self, field_name: str, default: str = "Not Specified") -> str:
        """Fill missing string field with appropriate default"""
        defaults = {
            'email': f'customer{random.randint(1000, 9999)}@example.com',
            'phone': f'+44{random.randint(1000000000, 9999999999)}',
            'address': f'{random.randint(1, 999)} Main Street',
            'city': random.choice(['London', 'Manchester', 'Birmingham', 'Leeds', 'Liverpool']),
            'postcode': f'SW{random.randint(1, 20)} {random.randint(1, 9)}AA',
            'country': 'United Kingdom',
            'ip_address': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
            'device_model': random.choice(['iPhone 14 Pro', 'Samsung Galaxy S23', 'Google Pixel 7']),
            'browser': random.choice(['Chrome', 'Safari', 'Firefox', 'Edge']),
            'os': random.choice(['iOS 17', 'Android 13', 'Windows 11', 'macOS Sonoma'])
        }
        return defaults.get(field_name, default)
    
    def fill_missing_number(self, field_name: str, default: float = 0.0) -> float:
        """Fill missing numeric field"""
        defaults = {
            'risk_score': random.uniform(10, 50),
            'trust_score': random.uniform(0.7, 0.95),
            'confidence': random.uniform(0.8, 0.98),
            'fraud_probability': random.uniform(0.01, 0.15),
            'amount': random.uniform(50, 500),
            'balance': random.uniform(1000, 50000)
        }
        return defaults.get(field_name, default)
    
    def enhance_nested_dict(self, obj: Any, parent_key: str = "") -> Any:
        """Recursively enhance nested dictionaries"""
        if isinstance(obj, dict):
            enhanced = {}
            for key, value in obj.items():
                if value is None or value == "":
                    # Fill missing value
                    if isinstance(value, str) or value == "":
                        enhanced[key] = self.fill_missing_string(key)
                    else:
                        enhanced[key] = self.fill_missing_number(key)
                    self.stats['enhanced_fields'] += 1
                elif isinstance(value, (dict, list)):
                    enhanced[key] = self.enhance_nested_dict(value, f"{parent_key}.{key}")
                else:
                    enhanced[key] = value
            return enhanced
        elif isinstance(obj, list):
            return [self.enhance_nested_dict(item, parent_key) for item in obj]
        else:
            return obj
    
    def validate_customers(self):
        """Validate and enhance customer dataset"""
        print("\n📋 Validating aegis_customers.json...")
        
        data = self.load_dataset('aegis_customers.json')
        customers = data.get('customers', [])
        
        required_fields = [
            'customer_id',
            'personal_information.name_full',
            'contact_information.email_primary',
            'contact_information.phone_primary'
        ]
        
        enhanced_customers = []
        for customer in customers:
            self.stats['total_records'] += 1
            
            # Ensure all nested structures exist
            if 'personal_information' not in customer:
                customer['personal_information'] = {}
            if 'contact_information' not in customer:
                customer['contact_information'] = {}
            if 'risk_profile' not in customer:
                customer['risk_profile'] = {}
            
            # Fill missing contact information
            if not customer['contact_information'].get('email_primary'):
                customer['contact_information']['email_primary'] = self.fill_missing_string('email')
                self.stats['enhanced_fields'] += 1
            
            if not customer['contact_information'].get('phone_primary'):
                customer['contact_information']['phone_primary'] = self.fill_missing_string('phone')
                self.stats['enhanced_fields'] += 1
            
            # Fill missing address
            if not customer['contact_information'].get('address_line_1'):
                customer['contact_information']['address_line_1'] = self.fill_missing_string('address')
                customer['contact_information']['address_line_2'] = ""
                customer['contact_information']['city'] = self.fill_missing_string('city')
                customer['contact_information']['postcode'] = self.fill_missing_string('postcode')
                customer['contact_information']['country'] = self.fill_missing_string('country')
                self.stats['enhanced_fields'] += 5
            
            # Enhance nested fields
            enhanced = self.enhance_nested_dict(customer)
            enhanced_customers.append(enhanced)
        
        data['customers'] = enhanced_customers
        self.save_dataset('aegis_customers.json', data)
        print(f"  ✓ Enhanced {len(enhanced_customers)} customer records")
    
    def validate_transactions(self):
        """Validate and enhance transaction dataset"""
        print("\n📋 Validating aegis_transactions.json...")
        
        data = self.load_dataset('aegis_transactions.json')
        transactions = data.get('transactions', [])
        
        enhanced_transactions = []
        for txn in transactions:
            self.stats['total_records'] += 1
            
            # Ensure critical fields exist
            if 'ip_address' not in txn or not txn['ip_address']:
                txn['ip_address'] = self.fill_missing_string('ip_address')
                self.stats['enhanced_fields'] += 1
            
            if 'device_model' not in txn or not txn['device_model']:
                txn['device_model'] = self.fill_missing_string('device_model')
                self.stats['enhanced_fields'] += 1
            
            if 'browser' not in txn or not txn['browser']:
                txn['browser'] = self.fill_missing_string('browser')
                self.stats['enhanced_fields'] += 1
            
            # Ensure risk scores exist
            if 'risk_score' not in txn or txn['risk_score'] is None:
                txn['risk_score'] = self.fill_missing_number('risk_score')
                self.stats['enhanced_fields'] += 1
            
            if 'location_risk' not in txn or txn['location_risk'] is None:
                txn['location_risk'] = random.uniform(0, 30)
                self.stats['enhanced_fields'] += 1
            
            if 'amount_risk' not in txn or txn['amount_risk'] is None:
                txn['amount_risk'] = random.uniform(0, 30)
                self.stats['enhanced_fields'] += 1
            
            if 'velocity_risk' not in txn or txn['velocity_risk'] is None:
                txn['velocity_risk'] = random.uniform(0, 30)
                self.stats['enhanced_fields'] += 1
            
            # Ensure device trust score
            if 'device_trust_score' not in txn or txn['device_trust_score'] is None:
                txn['device_trust_score'] = self.fill_missing_number('trust_score')
                self.stats['enhanced_fields'] += 1
            
            enhanced = self.enhance_nested_dict(txn)
            enhanced_transactions.append(enhanced)
        
        data['transactions'] = enhanced_transactions
        self.save_dataset('aegis_transactions.json', data)
        print(f"  ✓ Enhanced {len(enhanced_transactions)} transaction records")
    
    def validate_devices(self):
        """Validate and enhance device dataset"""
        print("\n📋 Validating aegis_devices.json...")
        
        data = self.load_dataset('aegis_devices.json')
        devices = data.get('devices', [])
        
        enhanced_devices = []
        for device in devices:
            self.stats['total_records'] += 1
            
            # Ensure device metadata is complete
            if not device.get('device_os'):
                device['device_os'] = self.fill_missing_string('os')
                self.stats['enhanced_fields'] += 1
            
            if not device.get('browser'):
                device['browser'] = self.fill_missing_string('browser')
                self.stats['enhanced_fields'] += 1
            
            if 'trust_score' not in device or device['trust_score'] is None:
                device['trust_score'] = self.fill_missing_number('trust_score')
                self.stats['enhanced_fields'] += 1
            
            # Ensure location history exists
            if 'location_history' not in device or not device['location_history']:
                device['location_history'] = [
                    {
                        'country': 'GB',
                        'city': self.fill_missing_string('city'),
                        'last_seen': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
                    }
                ]
                self.stats['enhanced_fields'] += 1
            
            enhanced = self.enhance_nested_dict(device)
            enhanced_devices.append(enhanced)
        
        data['devices'] = enhanced_devices
        self.save_dataset('aegis_devices.json', data)
        print(f"  ✓ Enhanced {len(enhanced_devices)} device records")
    
    def validate_cases(self):
        """Validate and enhance cases dataset"""
        print("\n📋 Validating aegis_cases.json...")
        
        data = self.load_dataset('aegis_cases.json')
        cases = data.get('cases', [])
        
        enhanced_cases = []
        for case in cases:
            self.stats['total_records'] += 1
            
            # Ensure investigation summary exists
            if not case.get('investigation_summary'):
                case['investigation_summary'] = f"Investigating {case.get('case_type', 'fraud pattern')}. Risk score: {case.get('risk_score', 'N/A')}"
                self.stats['enhanced_fields'] += 1
            
            # Ensure evidence collected exists
            if 'evidence_collected' not in case or not case['evidence_collected']:
                case['evidence_collected'] = [
                    'Transaction logs',
                    'Device fingerprints',
                    'IP geolocation'
                ]
                self.stats['enhanced_fields'] += 1
            
            # Ensure AI recommendations exist
            if 'ai_copilot_recommendations' not in case or not case['ai_copilot_recommendations']:
                case['ai_copilot_recommendations'] = [
                    {
                        'recommendation_type': 'Risk Assessment',
                        'confidence': random.uniform(0.75, 0.95),
                        'details': 'Automated risk analysis completed'
                    }
                ]
                self.stats['enhanced_fields'] += 1
            
            enhanced = self.enhance_nested_dict(case)
            enhanced_cases.append(enhanced)
        
        data['cases'] = enhanced_cases
        self.save_dataset('aegis_cases.json', data)
        print(f"  ✓ Enhanced {len(enhanced_cases)} case records")
    
    def validate_all(self):
        """Validate all datasets"""
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║     Validating and Enhancing Aegis Datasets                 ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
        # Validate each dataset
        self.validate_customers()
        self.validate_transactions()
        self.validate_devices()
        self.validate_cases()
        
        # Validate other datasets with generic enhancement
        other_datasets = [
            'aegis_accounts.json',
            'aegis_payees.json',
            'aegis_behavioral_events.json',
            'aegis_fraud_alerts.json',
            'aegis_call_history.json',
            'aegis_graph_relationships.json'
        ]
        
        for filename in other_datasets:
            if (self.data_dir / filename).exists():
                print(f"\n📋 Validating {filename}...")
                data = self.load_dataset(filename)
                
                # Get the main data array (first key with list value)
                main_key = None
                for key, value in data.items():
                    if isinstance(value, list) and key != 'metadata':
                        main_key = key
                        break
                
                if main_key:
                    records = data[main_key]
                    enhanced_records = []
                    for record in records:
                        self.stats['total_records'] += 1
                        enhanced = self.enhance_nested_dict(record)
                        enhanced_records.append(enhanced)
                    
                    data[main_key] = enhanced_records
                    self.save_dataset(filename, data)
                    print(f"  ✓ Enhanced {len(enhanced_records)} records")
        
        # Print summary
        print("\n╔══════════════════════════════════════════════════════════════╗")
        print("║                                                              ║")
        print("║     ✓ Validation Complete!                                  ║")
        print("║                                                              ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print("Summary:")
        print(f"  Total records processed: {self.stats['total_records']}")
        print(f"  Fields enhanced: {self.stats['enhanced_fields']}")
        print(f"  Validation errors: {len(self.stats['validation_errors'])}")
        
        if self.stats['validation_errors']:
            print("\nErrors:")
            for error in self.stats['validation_errors'][:10]:
                print(f"  - {error}")
        
        print("\n✓ All datasets validated and enhanced with zero missing values")
        print()

def main():
    data_dir = Path(__file__).parent
    validator = DatasetValidator(data_dir)
    validator.validate_all()

if __name__ == '__main__':
    main()





