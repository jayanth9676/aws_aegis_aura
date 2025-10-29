from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from configs import AppConfig

LOGGER = logging.getLogger("aegis.data.loader")


class DatasetValidationError(RuntimeError):
    """Raised when datasets are missing or schema validation fails."""


@dataclass(slots=True)
class DatasetBundle:
    customers: pd.DataFrame
    accounts: pd.DataFrame
    transactions: pd.DataFrame
    call_history: pd.DataFrame
    behavioral_events: pd.DataFrame
    fraud_alerts: pd.DataFrame
    metadata: Dict[str, any]

    def limit_rows(self, max_rows: Optional[int]) -> "DatasetBundle":
        if max_rows is None:
            return self
        return DatasetBundle(
            customers=self.customers.head(max_rows),
            accounts=self.accounts.head(max_rows),
            transactions=self.transactions.head(max_rows),
            call_history=self.call_history.head(max_rows),
            behavioral_events=self.behavioral_events.head(max_rows),
            fraud_alerts=self.fraud_alerts.head(max_rows),
            metadata=self.metadata,
        )


def _load_csv(path: Path, selected_columns: Optional[List[str]] = None) -> pd.DataFrame:
    if not path.exists():
        raise DatasetValidationError(f"Missing dataset: {path}")
    kwargs = {"usecols": selected_columns} if selected_columns else {}
    df = pd.read_csv(path, **kwargs)
    return df


def _validate_columns(df: pd.DataFrame, expected: List[str], table_name: str) -> None:
    missing = set(expected) - set(df.columns)
    if missing:
        raise DatasetValidationError(f"{table_name} missing columns: {sorted(missing)}")


def load_mule_datasets(config: AppConfig) -> Dict[str, pd.DataFrame]:
    """Load synthetic mule datasets if available.
    
    Args:
        config: Application configuration
        
    Returns:
        Dictionary of mule datasets
    """
    mule_dir = config.data_dir.parent / "new_datasets"
    
    if not mule_dir.exists():
        LOGGER.warning("Mule datasets directory not found: %s", mule_dir)
        return {}
    
    mule_datasets = {}
    
    # Load mule accounts
    mule_accounts_path = mule_dir / "synthetic_mule_accounts.csv"
    if mule_accounts_path.exists():
        mule_datasets['mule_accounts'] = _load_csv(mule_accounts_path)
        LOGGER.info("Loaded %d mule accounts", len(mule_datasets['mule_accounts']))
    
    # Load mule transactions
    mule_transactions_path = mule_dir / "synthetic_mule_transactions.csv"
    if mule_transactions_path.exists():
        mule_datasets['mule_transactions'] = _load_csv(mule_transactions_path)
        LOGGER.info("Loaded %d mule transactions", len(mule_datasets['mule_transactions']))
    
    # Load mule customers
    mule_customers_path = mule_dir / "synthetic_mule_customers.csv"
    if mule_customers_path.exists():
        mule_datasets['mule_customers'] = _load_csv(mule_customers_path)
        LOGGER.info("Loaded %d mule customers", len(mule_datasets['mule_customers']))
    
    return mule_datasets


def load_datasets(config: AppConfig, *, selected_columns: Optional[Dict[str, List[str]]] = None, 
                 include_mule_data: bool = True) -> DatasetBundle:
    """Load synthetic datasets with schema validation enforced by metadata."""

    selected_columns = selected_columns or {}

    if not config.metadata_path.exists():
        raise DatasetValidationError(f"Metadata file not found: {config.metadata_path}")

    LOGGER.info("Loading datasets from %s (Memory limit: %.1f GB, Chunk size: %d)",
                config.data_dir, config.max_memory_gb, config.chunk_size)

    metadata = json.loads(config.metadata_path.read_text())
    tables = metadata["tables"]

    def expected_cols(table_key: str) -> List[str]:
        return list(tables[table_key]["columns"].keys())

    customers = _load_csv(
        config.data_dir / "synthetic_aegis_customers.csv",
        selected_columns.get("customers"),
    )
    accounts = _load_csv(
        config.data_dir / "synthetic_aegis_accounts.csv",
        selected_columns.get("accounts"),
    )
    transactions = _load_csv(
        config.data_dir / "synthetic_aegis_transactions.csv",
        selected_columns.get("transactions"),
    )
    call_history = _load_csv(
        config.data_dir / "synthetic_aegis_call_history.csv",
        selected_columns.get("call_history"),
    )
    behavioral_events = _load_csv(
        config.data_dir / "synthetic_aegis_behavioral_events.csv",
        selected_columns.get("behavioral_events"),
    )
    fraud_alerts = _load_csv(
        config.data_dir / "synthetic_aegis_fraud_alerts.csv",
        selected_columns.get("fraud_alerts"),
    )

    _validate_columns(customers, expected_cols("aegis_customers"), "customers")
    _validate_columns(accounts, expected_cols("aegis_accounts"), "accounts")
    _validate_columns(transactions, expected_cols("aegis_transactions"), "transactions")
    _validate_columns(call_history, expected_cols("aegis_call_history"), "call_history")
    _validate_columns(behavioral_events, expected_cols("aegis_behavioral_events"), "behavioral_events")
    _validate_columns(fraud_alerts, expected_cols("aegis_fraud_alerts"), "fraud_alerts")

    # Merge with mule data if available and requested
    if include_mule_data:
        mule_datasets = load_mule_datasets(config)
        
        if mule_datasets:
            LOGGER.info("Merging mule data with existing datasets")
            
            # Merge accounts
            if 'mule_accounts' in mule_datasets:
                # Ensure mule accounts have required columns
                mule_accounts = mule_datasets['mule_accounts'].copy()
                required_account_cols = expected_cols("aegis_accounts")
                for col in required_account_cols:
                    if col not in mule_accounts.columns:
                        if col == 'is_mule_account':
                            mule_accounts[col] = True
                        else:
                            mule_accounts[col] = 0  # Default value
                
                accounts = pd.concat([accounts, mule_accounts[required_account_cols]], ignore_index=True)
                LOGGER.info("Merged %d mule accounts", len(mule_accounts))
            
            # Merge transactions
            if 'mule_transactions' in mule_datasets:
                mule_transactions = mule_datasets['mule_transactions'].copy()
                required_transaction_cols = expected_cols("aegis_transactions")
                for col in required_transaction_cols:
                    if col not in mule_transactions.columns:
                        if col == 'is_fraud':
                            mule_transactions[col] = 1
                        else:
                            mule_transactions[col] = 0  # Default value
                
                transactions = pd.concat([transactions, mule_transactions[required_transaction_cols]], ignore_index=True)
                LOGGER.info("Merged %d mule transactions", len(mule_transactions))
            
            # Merge customers
            if 'mule_customers' in mule_datasets:
                mule_customers = mule_datasets['mule_customers'].copy()
                required_customer_cols = expected_cols("aegis_customers")
                for col in required_customer_cols:
                    if col not in mule_customers.columns:
                        if col == 'is_vulnerable':
                            mule_customers[col] = True
                        else:
                            mule_customers[col] = 0  # Default value
                
                customers = pd.concat([customers, mule_customers[required_customer_cols]], ignore_index=True)
                LOGGER.info("Merged %d mule customers", len(mule_customers))

    bundle = DatasetBundle(
        customers=customers,
        accounts=accounts,
        transactions=transactions,
        call_history=call_history,
        behavioral_events=behavioral_events,
        fraud_alerts=fraud_alerts,
        metadata=metadata,
    )

    if config.max_rows is not None:
        bundle = bundle.limit_rows(config.max_rows)

    return bundle


