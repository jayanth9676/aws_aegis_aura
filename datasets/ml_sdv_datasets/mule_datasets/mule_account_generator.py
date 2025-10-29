"""Synthetic mule account generator for enhanced fraud detection training."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

LOGGER = logging.getLogger("aegis.datasets.mule_generator")


def generate_mule_accounts(n_mule_accounts: int = 1000, 
                          random_state: int = 42) -> pd.DataFrame:
    """Generate realistic mule account patterns.
    
    Mule account characteristics:
    - High in_degree (many incoming transfers)
    - High out_degree (rapid fund dispersion)
    - Short account lifetime
    - New customers with minimal history
    - Rapid transaction velocity
    - Cross-border patterns
    
    Args:
        n_mule_accounts: Number of mule accounts to generate
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with mule account data
    """
    np.random.seed(random_state)
    
    LOGGER.info("Generating %d mule accounts", n_mule_accounts)
    
    mule_accounts = []
    for i in range(n_mule_accounts):
        # Account characteristics
        account_id = f"mule_{i:06d}"
        customer_id = f"mule_cust_{i:06d}"
        
        # Account age (new accounts are more likely to be mules)
        account_age_days = np.random.choice(
            [1, 2, 3, 4, 5, 7, 10, 14, 21, 30, 45, 60, 90],
            p=[0.16, 0.13, 0.11, 0.09, 0.09, 0.11, 0.09, 0.07, 0.05, 0.04, 0.03, 0.02, 0.01]
        )
        
        # Account limits (lower than normal accounts)
        daily_limit = np.random.uniform(500, 2000)
        monthly_limit = np.random.uniform(5000, 20000)
        
        # Network patterns (high connectivity)
        in_degree = np.random.randint(10, 50)  # Many incoming transfers
        out_degree = np.random.randint(15, 60)  # Rapid dispersion
        total_degree = in_degree + out_degree
        
        # Transaction patterns
        avg_incoming_amount = np.random.uniform(200, 5000)
        avg_outgoing_amount = np.random.uniform(150, 4500)
        transaction_velocity = np.random.uniform(5, 20)  # Transactions per day
        
        # Risk indicators
        risk_score = np.random.uniform(0.7, 0.95)  # High risk
        vulnerability_score = np.random.uniform(0.6, 0.9)
        
        # Geographic patterns (cross-border activity)
        countries = ["UK", "US", "CA", "AU", "DE", "FR", "IT", "ES", "NL", "BE"]
        primary_country = np.random.choice(countries, p=[0.3, 0.2, 0.1, 0.1, 0.08, 0.08, 0.05, 0.04, 0.03, 0.02])
        
        account = {
            "account_id": account_id,
            "customer_id": customer_id,
            "is_mule_account": True,
            "account_type": "personal_current",
            "account_age_days": account_age_days,
            "daily_limit": round(daily_limit, 2),
            "monthly_limit": round(monthly_limit, 2),
            
            # Network characteristics
            "in_degree": in_degree,
            "out_degree": out_degree,
            "total_degree": total_degree,
            "avg_incoming_amount": round(avg_incoming_amount, 2),
            "avg_outgoing_amount": round(avg_outgoing_amount, 2),
            "transaction_velocity": round(transaction_velocity, 2),
            
            # Risk indicators
            "risk_score": round(risk_score, 3),
            "vulnerability_score": round(vulnerability_score, 3),
            "primary_country": primary_country,
            
            # Additional mule indicators
            "is_new_customer": account_age_days <= 30,
            "high_velocity": transaction_velocity > 10,
            "cross_border_activity": primary_country != "UK",
            "structuring_indicator": avg_incoming_amount < 10000,  # Below reporting threshold
        }
        
        mule_accounts.append(account)
    
    df = pd.DataFrame(mule_accounts)
    LOGGER.info("Generated %d mule accounts with average degree %d", 
                len(df), df['total_degree'].mean())
    
    return df


def generate_mule_transaction_patterns(mule_accounts: pd.DataFrame, 
                                     n_transactions_per_mule: int = 50,
                                     random_state: int = 42) -> pd.DataFrame:
    """Generate realistic transaction flows for mule accounts.
    
    Transaction patterns:
    - Pattern 1: Rapid fund layering (receive → split → send)
    - Pattern 2: Cross-account chains (A→B→C→D)
    - Pattern 3: Structuring (amounts just below reporting thresholds)
    - Pattern 4: Time-based patterns (night/weekend activity)
    
    Args:
        mule_accounts: DataFrame of mule accounts
        n_transactions_per_mule: Number of transactions per mule account
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with mule transaction data
    """
    np.random.seed(random_state)
    
    LOGGER.info("Generating transactions for %d mule accounts", len(mule_accounts))
    
    transactions = []
    transaction_id_counter = 1000000  # Start from high number to avoid conflicts
    
    # Generate victim accounts (sources of fraud)
    n_victims = len(mule_accounts) * 2
    victim_accounts = [f"victim_{i:06d}" for i in range(n_victims)]
    
    # Generate final destination accounts
    n_destinations = len(mule_accounts) * 3
    destination_accounts = [f"final_{i:06d}" for i in range(n_destinations)]
    
    for _, mule in mule_accounts.iterrows():
        mule_id = mule['account_id']
        
        # Generate incoming transactions (fraud victims → mule)
        n_incoming = n_transactions_per_mule // 2
        for _ in range(n_incoming):
            transaction_id = f"txn_{transaction_id_counter:08d}"
            transaction_id_counter += 1
            
            # Amount structuring (below $10k threshold)
            amount = np.random.uniform(500, 9500)
            
            # Time patterns (more activity during off-hours)
            hour_probs = [0.025, 0.017, 0.017, 0.017, 0.017, 0.017, 0.025, 0.033, 0.041, 0.050, 0.058, 0.066,
                         0.074, 0.066, 0.058, 0.050, 0.041, 0.033, 0.041, 0.050, 0.058, 0.066, 0.050, 0.033]
            hour_probs = np.array(hour_probs) / sum(hour_probs)  # Normalize to sum to 1
            hour = np.random.choice(list(range(24)), p=hour_probs)
            
            # Weekend activity (higher for mules)
            is_weekend = np.random.choice([0, 1], p=[0.7, 0.3])
            
            incoming = {
                "transaction_id": transaction_id,
                "source_account_id": np.random.choice(victim_accounts),
                "destination_account_id": mule_id,
                "amount": round(amount, 2),
                "is_fraud": 1,
                "transaction_type": "push_payment",
                "payment_channel": np.random.choice(["online", "mobile", "phone"], p=[0.6, 0.3, 0.1]),
                "hour": hour,
                "is_weekend": is_weekend,
                "is_night": 1 if hour in list(range(22, 24)) + list(range(0, 6)) else 0,
                "risk_score": np.random.uniform(0.7, 0.95),
                "known_device": 0,  # Mules often use new devices
                "is_flagged": np.random.choice([0, 1], p=[0.3, 0.7]),  # High flag rate
            }
            transactions.append(incoming)
        
        # Generate outgoing transactions (mule → other mules/final destination)
        n_outgoing = n_transactions_per_mule // 2
        for _ in range(n_outgoing):
            transaction_id = f"txn_{transaction_id_counter:08d}"
            transaction_id_counter += 1
            
            # Amount (slightly less than incoming to account for fees)
            amount = np.random.uniform(400, 9000)
            
            # Time patterns
            hour_probs = [0.025, 0.017, 0.017, 0.017, 0.017, 0.017, 0.025, 0.033, 0.041, 0.050, 0.058, 0.066,
                         0.074, 0.066, 0.058, 0.050, 0.041, 0.033, 0.041, 0.050, 0.058, 0.066, 0.050, 0.033]
            hour_probs = np.array(hour_probs) / sum(hour_probs)  # Normalize to sum to 1
            hour = np.random.choice(list(range(24)), p=hour_probs)
            
            is_weekend = np.random.choice([0, 1], p=[0.7, 0.3])
            
            # Destination (mix of other mules and final destinations)
            if np.random.random() < 0.3:  # 30% to other mules
                dest_id = np.random.choice([acc for acc in mule_accounts['account_id'] if acc != mule_id])
            else:  # 70% to final destinations
                dest_id = np.random.choice(destination_accounts)
            
            outgoing = {
                "transaction_id": transaction_id,
                "source_account_id": mule_id,
                "destination_account_id": dest_id,
                "amount": round(amount, 2),
                "is_fraud": 1,
                "transaction_type": "push_payment",
                "payment_channel": np.random.choice(["online", "mobile", "phone"], p=[0.6, 0.3, 0.1]),
                "hour": hour,
                "is_weekend": is_weekend,
                "is_night": 1 if hour in list(range(22, 24)) + list(range(0, 6)) else 0,
                "risk_score": np.random.uniform(0.7, 0.95),
                "known_device": 0,
                "is_flagged": np.random.choice([0, 1], p=[0.3, 0.7]),
            }
            transactions.append(outgoing)
    
    df = pd.DataFrame(transactions)
    LOGGER.info("Generated %d mule transactions with average amount %.2f", 
                len(df), df['amount'].mean())
    
    return df


def generate_mule_customers(mule_accounts: pd.DataFrame, 
                          random_state: int = 42) -> pd.DataFrame:
    """Generate customer data for mule accounts.
    
    Args:
        mule_accounts: DataFrame of mule accounts
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with mule customer data
    """
    np.random.seed(random_state)
    
    LOGGER.info("Generating customer data for %d mule accounts", len(mule_accounts))
    
    customers = []
    for _, account in mule_accounts.iterrows():
        customer_id = account['customer_id']
        
        # Age (younger customers more likely to be mules)
        age = np.random.choice(
            [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35],
            p=[0.05, 0.06, 0.07, 0.08, 0.08, 0.08, 0.08, 0.08, 0.07, 0.07, 0.06, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01, 0.01]
        )
        
        # Income (lower income more likely to be mules)
        annual_income = np.random.uniform(15000, 35000)
        
        # Risk profile
        risk_profile = np.random.choice(["high", "critical"], p=[0.7, 0.3])
        vulnerability_score = account['vulnerability_score']
        
        # Digital literacy (lower for mules)
        digital_literacy_level = np.random.choice(["low", "medium"], p=[0.6, 0.4])
        
        customer = {
            "customer_id": customer_id,
            "age": age,
            "annual_income": round(annual_income, 2),
            "is_vulnerable": True,
            "vulnerability_score": vulnerability_score,
            "credit_score": np.random.randint(400, 650),  # Lower credit scores
            "digital_literacy_level": digital_literacy_level,
            "risk_profile": risk_profile,
            "customer_tenure_years": account['account_age_days'] / 365.0,  # Very new
        }
        
        customers.append(customer)
    
    df = pd.DataFrame(customers)
    LOGGER.info("Generated %d mule customers with average age %.1f", 
                len(df), df['age'].mean())
    
    return df


def generate_mule_metadata(mule_accounts: pd.DataFrame, 
                         mule_transactions: pd.DataFrame,
                         mule_customers: pd.DataFrame) -> Dict[str, any]:
    """Generate metadata for mule datasets.
    
    Args:
        mule_accounts: DataFrame of mule accounts
        mule_transactions: DataFrame of mule transactions
        mule_customers: DataFrame of mule customers
        
    Returns:
        Dictionary with metadata
    """
    metadata = {
        "dataset_type": "synthetic_mule_data",
        "generation_timestamp": pd.Timestamp.now().isoformat(),
        "statistics": {
            "n_mule_accounts": len(mule_accounts),
            "n_mule_transactions": len(mule_transactions),
            "n_mule_customers": len(mule_customers),
            "avg_transactions_per_mule": len(mule_transactions) / len(mule_accounts),
            "avg_incoming_amount": mule_transactions[mule_transactions['destination_account_id'].str.startswith('mule_')]['amount'].mean(),
            "avg_outgoing_amount": mule_transactions[mule_transactions['source_account_id'].str.startswith('mule_')]['amount'].mean(),
            "fraud_rate": mule_transactions['is_fraud'].mean(),
            "weekend_activity_rate": mule_transactions['is_weekend'].mean(),
            "night_activity_rate": mule_transactions['is_night'].mean(),
        },
        "mule_characteristics": {
            "avg_account_age_days": mule_accounts['account_age_days'].mean(),
            "avg_in_degree": mule_accounts['in_degree'].mean(),
            "avg_out_degree": mule_accounts['out_degree'].mean(),
            "avg_transaction_velocity": mule_accounts['transaction_velocity'].mean(),
            "new_customer_rate": mule_accounts['is_new_customer'].mean(),
            "high_velocity_rate": mule_accounts['high_velocity'].mean(),
            "cross_border_rate": mule_accounts['cross_border_activity'].mean(),
            "structuring_rate": mule_accounts['structuring_indicator'].mean(),
        },
        "schema": {
            "mule_accounts": list(mule_accounts.columns),
            "mule_transactions": list(mule_transactions.columns),
            "mule_customers": list(mule_customers.columns),
        }
    }
    
    return metadata


def generate_all_mule_data(n_mule_accounts: int = 1000,
                          n_transactions_per_mule: int = 50,
                          output_dir: Path = Path("datasets/new_datasets"),
                          random_state: int = 42) -> Dict[str, Path]:
    """Generate complete mule dataset and save to files.
    
    Args:
        n_mule_accounts: Number of mule accounts to generate
        n_transactions_per_mule: Number of transactions per mule account
        output_dir: Directory to save generated data
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary of saved file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    LOGGER.info("Generating complete mule dataset: %d accounts, %d transactions each", 
                n_mule_accounts, n_transactions_per_mule)
    
    # Generate datasets
    mule_accounts = generate_mule_accounts(n_mule_accounts, random_state)
    mule_transactions = generate_mule_transaction_patterns(mule_accounts, n_transactions_per_mule, random_state)
    mule_customers = generate_mule_customers(mule_accounts, random_state)
    
    # Generate metadata
    metadata = generate_mule_metadata(mule_accounts, mule_transactions, mule_customers)
    
    # Save to files
    accounts_path = output_dir / "synthetic_mule_accounts.csv"
    transactions_path = output_dir / "synthetic_mule_transactions.csv"
    customers_path = output_dir / "synthetic_mule_customers.csv"
    metadata_path = output_dir / "mule_metadata.json"
    
    mule_accounts.to_csv(accounts_path, index=False)
    mule_transactions.to_csv(transactions_path, index=False)
    mule_customers.to_csv(customers_path, index=False)
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    LOGGER.info("Saved mule datasets to %s", output_dir)
    LOGGER.info("Files created:")
    LOGGER.info("  - %s (%d accounts)", accounts_path, len(mule_accounts))
    LOGGER.info("  - %s (%d transactions)", transactions_path, len(mule_transactions))
    LOGGER.info("  - %s (%d customers)", customers_path, len(mule_customers))
    LOGGER.info("  - %s (metadata)", metadata_path)
    
    return {
        "accounts": accounts_path,
        "transactions": transactions_path,
        "customers": customers_path,
        "metadata": metadata_path,
    }


if __name__ == "__main__":
    # Generate mule data when run directly
    logging.basicConfig(level=logging.INFO)
    generate_all_mule_data()
