"""
Data normalization module to convert broker-specific formats to canonical schemas.

Canonical Schemas:
1. trades: client_id, broker, account, date, isin, symbol, action, qty, price, 
          trade_value, total_charges, exchange, currency
2. capital_gains: client_id, broker, account, symbol, isin, qty, sale_date, 
                 sale_rate, sale_value, sale_expenses, purchase_date, 
                 purchase_rate_considered, purchase_value, purchase_expenses, 
                 pnl, section
"""
import pandas as pd
from decimal import Decimal
from typing import Dict, List
from datetime import datetime
from decimal_utils import to_decimal, round_decimal


def normalize_trade_book(ingested_data: Dict) -> pd.DataFrame:
    """
    Normalize a trade book file to canonical trades schema.
    
    Args:
        ingested_data: Dictionary from ingestion module
    
    Returns:
        DataFrame with canonical trades schema
    """
    df = ingested_data['data'].copy()
    client_id = ingested_data['client_id']
    broker = ingested_data['broker']
    account = ingested_data['metadata'].get('account', '')
    
    if df.empty:
        return create_empty_trades_df()
    
    # Map columns (handle various possible column names)
    column_mapping = {}
    
    for col in df.columns:
        col_lower = str(col).strip().lower()
        
        if col_lower == 'date':
            column_mapping['date'] = col
        elif col_lower in ['stock', 'symbol', 'stock symbol']:
            column_mapping['symbol'] = col
        elif col_lower == 'action':
            column_mapping['action'] = col
        elif col_lower in ['qty', 'quantity']:
            column_mapping['qty'] = col
        elif col_lower == 'price':
            column_mapping['price'] = col
        elif col_lower in ['trade value', 'tradevalue']:
            column_mapping['trade_value'] = col
        elif col_lower == 'exchange':
            column_mapping['exchange'] = col
        elif 'dp id' in col_lower or 'client dp id' in col_lower:
            column_mapping['dp_id'] = col
        elif col_lower == 'currency':
            column_mapping['currency'] = col
        elif 'charges' in col_lower or 'brokerage' in col_lower:
            # Aggregate all charge columns
            if 'charges_cols' not in column_mapping:
                column_mapping['charges_cols'] = []
            column_mapping['charges_cols'].append(col)
    
    # Create normalized DataFrame
    normalized_rows = []
    
    for idx, row in df.iterrows():
        try:
            # Extract values
            date_val = row.get(column_mapping.get('date', ''), None)
            symbol_val = row.get(column_mapping.get('symbol', ''), None)
            action_val = row.get(column_mapping.get('action', ''), None)
            qty_val = row.get(column_mapping.get('qty', ''), None)
            price_val = row.get(column_mapping.get('price', ''), None)
            trade_value_val = row.get(column_mapping.get('trade_value', ''), None)
            exchange_val = row.get(column_mapping.get('exchange', ''), None)
            dp_id_val = row.get(column_mapping.get('dp_id', ''), None)
            currency_val = row.get(column_mapping.get('currency', ''), 'USD')
            
            # Skip if essential fields are missing
            if not symbol_val or not action_val or not qty_val:
                continue
            
            # Parse date
            if isinstance(date_val, datetime):
                date_parsed = date_val
            elif isinstance(date_val, str):
                try:
                    date_parsed = pd.to_datetime(date_val)
                except:
                    date_parsed = None
            else:
                date_parsed = None
            
            # Convert to Decimal
            qty = to_decimal(qty_val)
            price = to_decimal(price_val)
            trade_value = to_decimal(trade_value_val)
            
            # Calculate total charges
            total_charges = Decimal("0")
            if 'charges_cols' in column_mapping:
                for charge_col in column_mapping['charges_cols']:
                    charge_val = row.get(charge_col, 0)
                    if charge_val:
                        total_charges += to_decimal(charge_val)
            
            # Create normalized row
            normalized_row = {
                'client_id': client_id,
                'broker': broker,
                'account': account,
                'date': date_parsed,
                'isin': None,  # Not available in trade book typically
                'symbol': str(symbol_val).strip(),
                'action': str(action_val).strip().capitalize(),
                'qty': qty,
                'price': round_decimal(price),
                'trade_value': round_decimal(trade_value),
                'total_charges': round_decimal(total_charges),
                'exchange': str(exchange_val).strip() if exchange_val else '',
                'currency': str(currency_val).strip() if currency_val else 'USD'
            }
            
            normalized_rows.append(normalized_row)
            
        except Exception as e:
            # Skip rows with errors
            print(f"Warning: Could not normalize trade row {idx}: {e}")
            continue
    
    if not normalized_rows:
        return create_empty_trades_df()
    
    result_df = pd.DataFrame(normalized_rows)
    
    # Ensure correct dtypes
    result_df['qty'] = result_df['qty'].apply(lambda x: x if isinstance(x, Decimal) else to_decimal(x))
    result_df['price'] = result_df['price'].apply(lambda x: x if isinstance(x, Decimal) else to_decimal(x))
    result_df['trade_value'] = result_df['trade_value'].apply(lambda x: x if isinstance(x, Decimal) else to_decimal(x))
    result_df['total_charges'] = result_df['total_charges'].apply(lambda x: x if isinstance(x, Decimal) else to_decimal(x))
    
    return result_df


def normalize_capital_gains(ingested_data: Dict) -> pd.DataFrame:
    """
    Normalize a capital gains file to canonical schema.
    
    Args:
        ingested_data: Dictionary from ingestion module
    
    Returns:
        DataFrame with canonical capital_gains schema
    """
    df = ingested_data['data'].copy()
    client_id = ingested_data['client_id']
    broker = ingested_data['broker']
    account = ingested_data['metadata'].get('account', '')
    
    if df.empty:
        return create_empty_capital_gains_df()
    
    # Map columns
    column_mapping = {}
    
    for col in df.columns:
        col_lower = str(col).strip().lower()
        
        if col_lower in ['stock symbol', 'symbol', 'stock']:
            column_mapping['symbol'] = col
        elif col_lower == 'isin':
            column_mapping['isin'] = col
        elif col_lower == 'qty':
            column_mapping['qty'] = col
        elif col_lower == 'sale date':
            column_mapping['sale_date'] = col
        elif col_lower == 'sale rate':
            column_mapping['sale_rate'] = col
        elif col_lower == 'sale value':
            column_mapping['sale_value'] = col
        elif col_lower == 'sale expenses':
            column_mapping['sale_expenses'] = col
        elif col_lower == 'purchase date':
            column_mapping['purchase_date'] = col
        elif col_lower == 'purchase rate considered':
            column_mapping['purchase_rate'] = col
        elif col_lower == 'purchase value':
            column_mapping['purchase_value'] = col
        elif col_lower == 'purchase expenses':
            column_mapping['purchase_expenses'] = col
        elif 'profit/loss' in col_lower:
            column_mapping['pnl'] = col
        elif col_lower == 'st/lt':
            column_mapping['section'] = col
    
    # Create normalized DataFrame
    normalized_rows = []
    
    for idx, row in df.iterrows():
        try:
            # Extract values
            symbol_val = row.get(column_mapping.get('symbol', ''), None)
            isin_val = row.get(column_mapping.get('isin', ''), None)
            qty_val = row.get(column_mapping.get('qty', ''), None)
            
            # Skip if essential fields are missing
            if not symbol_val or not qty_val:
                continue
            
            # Parse dates
            sale_date_val = row.get(column_mapping.get('sale_date', ''), None)
            purchase_date_val = row.get(column_mapping.get('purchase_date', ''), None)
            
            if isinstance(sale_date_val, datetime):
                sale_date = sale_date_val
            elif isinstance(sale_date_val, str):
                try:
                    sale_date = pd.to_datetime(sale_date_val)
                except:
                    sale_date = None
            else:
                sale_date = None
            
            if isinstance(purchase_date_val, datetime):
                purchase_date = purchase_date_val
            elif isinstance(purchase_date_val, str):
                try:
                    purchase_date = pd.to_datetime(purchase_date_val)
                except:
                    purchase_date = None
            else:
                purchase_date = None
            
            # Convert to Decimal
            qty = to_decimal(qty_val)
            sale_rate = to_decimal(row.get(column_mapping.get('sale_rate', ''), 0))
            sale_value = to_decimal(row.get(column_mapping.get('sale_value', ''), 0))
            sale_expenses = to_decimal(row.get(column_mapping.get('sale_expenses', ''), 0))
            purchase_rate = to_decimal(row.get(column_mapping.get('purchase_rate', ''), 0))
            purchase_value = to_decimal(row.get(column_mapping.get('purchase_value', ''), 0))
            purchase_expenses = to_decimal(row.get(column_mapping.get('purchase_expenses', ''), 0))
            pnl = to_decimal(row.get(column_mapping.get('pnl', ''), 0))
            
            section_val = row.get(column_mapping.get('section', ''), 'ST')
            
            # Create normalized row
            normalized_row = {
                'client_id': client_id,
                'broker': broker,
                'account': account,
                'symbol': str(symbol_val).strip(),
                'isin': str(isin_val).strip() if isin_val else None,
                'qty': qty,
                'sale_date': sale_date,
                'sale_rate': round_decimal(sale_rate),
                'sale_value': round_decimal(sale_value),
                'sale_expenses': round_decimal(sale_expenses),
                'purchase_date': purchase_date,
                'purchase_rate_considered': round_decimal(purchase_rate),
                'purchase_value': round_decimal(purchase_value),
                'purchase_expenses': round_decimal(purchase_expenses),
                'pnl': round_decimal(pnl),
                'section': str(section_val).strip().upper()
            }
            
            normalized_rows.append(normalized_row)
            
        except Exception as e:
            print(f"Warning: Could not normalize capital gains row {idx}: {e}")
            continue
    
    if not normalized_rows:
        return create_empty_capital_gains_df()
    
    result_df = pd.DataFrame(normalized_rows)
    
    # Ensure correct dtypes for Decimal columns
    decimal_cols = ['qty', 'sale_rate', 'sale_value', 'sale_expenses',
                   'purchase_rate_considered', 'purchase_value', 
                   'purchase_expenses', 'pnl']
    
    for col in decimal_cols:
        result_df[col] = result_df[col].apply(lambda x: x if isinstance(x, Decimal) else to_decimal(x))
    
    return result_df


def create_empty_trades_df() -> pd.DataFrame:
    """Create empty DataFrame with trades schema."""
    return pd.DataFrame(columns=[
        'client_id', 'broker', 'account', 'date', 'isin', 'symbol', 
        'action', 'qty', 'price', 'trade_value', 'total_charges', 
        'exchange', 'currency'
    ])


def create_empty_capital_gains_df() -> pd.DataFrame:
    """Create empty DataFrame with capital_gains schema."""
    return pd.DataFrame(columns=[
        'client_id', 'broker', 'account', 'symbol', 'isin', 'qty', 
        'sale_date', 'sale_rate', 'sale_value', 'sale_expenses',
        'purchase_date', 'purchase_rate_considered', 'purchase_value',
        'purchase_expenses', 'pnl', 'section'
    ])


def normalize_all_files(ingested_files: List[Dict]) -> Dict[str, pd.DataFrame]:
    """
    Normalize all ingested files.
    
    Args:
        ingested_files: List of ingested file dictionaries
    
    Returns:
        Dictionary with 'trades' and 'capital_gains' DataFrames
    """
    all_trades = []
    all_capital_gains = []
    
    for file_data in ingested_files:
        file_type = file_data['file_type']
        
        try:
            if file_type == 'trade_book':
                trades_df = normalize_trade_book(file_data)
                if not trades_df.empty:
                    all_trades.append(trades_df)
            
            elif file_type == 'capital_gains':
                cg_df = normalize_capital_gains(file_data)
                if not cg_df.empty:
                    all_capital_gains.append(cg_df)
        
        except Exception as e:
            print(f"Error normalizing {file_data['file_path']}: {e}")
            continue
    
    # Concatenate all
    if all_trades:
        trades_combined = pd.concat(all_trades, ignore_index=True)
    else:
        trades_combined = create_empty_trades_df()
    
    if all_capital_gains:
        cg_combined = pd.concat(all_capital_gains, ignore_index=True)
    else:
        cg_combined = create_empty_capital_gains_df()
    
    return {
        'trades': trades_combined,
        'capital_gains': cg_combined
    }
