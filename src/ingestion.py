"""
Data ingestion module for reading broker export files.
Handles Excel files with tab-separated data within single columns.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import openpyxl
from decimal import Decimal


def detect_file_type(file_path: str) -> Optional[str]:
    """
    Detect the type of broker export file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        One of: 'trade_book', 'capital_gains', 'holdings', or None
    """
    file_name = os.path.basename(file_path).lower()
    
    # Trade book detection (support more generic names)
    if ('tradebook' in file_name or 'trade_book' in file_name or
        file_name.startswith('trades') or 'trades' in file_name or 'trade' in file_name):
        return 'trade_book'
    # Capital gains detection (support more generic names)
    elif ('capital' in file_name and 'gain' in file_name) or (
        file_name.startswith('capital_gains') or 'capital_gains' in file_name or 'capgain' in file_name or 'cg' in file_name):
        return 'capital_gains'
    elif 'holding' in file_name:
        return 'holdings'
    
    return None


def extract_client_broker_from_path(file_path: str) -> Tuple[str, str]:
    """
    Extract client_id and broker from file path.
    
    Expected structures: 
    - .../C001/Charles_Schwab/file.xlsx (broker as subfolder)
    - .../C001/Uploaded_Files/file.xlsx (generic upload folder)
    - .../C001/tradeBook_HDFC_Bank.xlsx (broker in filename)
    
    Args:
        file_path: Full path to file
    
    Returns:
        Tuple of (client_id, broker)
    """
    path_parts = Path(file_path).parts
    file_name = Path(file_path).stem  # filename without extension
    
    # Find client folder (e.g., C001, C002)
    client_id = None
    broker = None
    
    for i, part in enumerate(path_parts):
        if re.match(r'^C\d{3,}$', part):
            client_id = part
            # Check if next part is a subdirectory (not a file)
            if i + 1 < len(path_parts) and i + 2 < len(path_parts):
                # Has a subfolder between client and file
                subfolder = path_parts[i + 1]
                # Ignore generic folder names like "Uploaded_Files"
                if subfolder not in ['Uploaded_Files', 'uploads', 'files', 'data']:
                    broker = subfolder
            break
    
    if not client_id:
        raise ValueError(f"Could not extract client_id from path: {file_path}")
    
    # If broker not found in path, try to extract from filename
    if not broker:
        # Look for pattern: accountNumber_type or type_BrokerName
        if '_' in file_name:
            parts = file_name.split('_')
            # If multiple parts, check for broker names
            for part in parts:
                part_clean = part.strip().lower()
                # Check for known broker keywords
                if any(keyword in part_clean for keyword in ['zerodha', 'schwab', 'fidelity', 'hdfc', 'icici', 'groww']):
                    broker = part.replace('_', ' ')
                    break
        
        # Still no broker? Try to extract account number as identifier
        if not broker:
            # Look for numeric account patterns in filename
            account_match = re.search(r'(\d{10,})', file_name)
            if account_match:
                broker = f"Account_{account_match.group(1)[:6]}"
            else:
                broker = "Platform_Unknown"
    
    return client_id, broker


def read_csv_file(file_path: str) -> pd.DataFrame:
    """
    Read CSV file and handle various delimiters.
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        DataFrame with CSV data
    """
    try:
        # Try reading with automatic delimiter detection
        df = pd.read_csv(file_path, sep=None, engine='python')
        return df
    except:
        # Try common delimiters
        for delimiter in [',', '\t', ';', '|']:
            try:
                df = pd.read_csv(file_path, sep=delimiter)
                if len(df.columns) > 1:  # Valid if we got multiple columns
                    return df
            except:
                continue
        
        # If all fail, return empty DataFrame
        return pd.DataFrame()


def read_excel_with_tab_detection(file_path: str) -> pd.DataFrame:
    """
    Read Excel file and detect if data is tab-separated within a single column.
    If so, split the data into proper columns.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        DataFrame with properly separated columns
    """
    # Load workbook
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    
    # Get all rows as list
    rows = list(ws.iter_rows(values_only=True))
    
    if not rows:
        return pd.DataFrame()
    
    # Check if data is tab-separated by looking at first few rows
    # Sometimes row 1 is just a header without tabs, so check rows 1-3
    has_tabs = False
    for i in range(min(3, len(rows))):
        cell = rows[i][0]
        if cell and isinstance(cell, str) and '\t' in cell:
            has_tabs = True
            break
    
    if has_tabs:
        # Tab-separated format detected
        split_rows = []
        for row in rows:
            if row[0]:
                cell_value = str(row[0])
                if '\t' in cell_value:
                    # Split on tabs and remove trailing empty strings
                    split_values = cell_value.split('\t')
                    # Remove trailing empty values
                    while split_values and not split_values[-1].strip():
                        split_values.pop()
                    split_rows.append(split_values)
                else:
                    # Row without tabs (like first row "Account")
                    split_rows.append([cell_value])
        
        # Create DataFrame with proper structure
        if split_rows:
            # Find max columns
            max_cols = max(len(row) for row in split_rows)
            # Pad rows to same length
            padded_rows = [row + [''] * (max_cols - len(row)) for row in split_rows]
            df = pd.DataFrame(padded_rows)
            return df
        else:
            return pd.DataFrame()
    else:
        # Normal Excel format
        df = pd.DataFrame(rows)
        if len(df) > 0:
            df.columns = df.iloc[0]
            df = df.iloc[1:]
            df = df.reset_index(drop=True)
        return df


def find_data_start_row(df: pd.DataFrame, file_type: str) -> int:
    """
    Find the row where actual data starts (after metadata rows).
    
    Args:
        df: DataFrame
        file_type: Type of file ('trade_book', 'capital_gains')
    
    Returns:
        Index of first data row
    """
    if file_type == 'trade_book':
        # Look for row with "Date" column
        for idx, row in df.iterrows():
            if row.iloc[0] and str(row.iloc[0]).strip().lower() == 'date':
                return idx
    elif file_type == 'capital_gains':
        # Look for row with "Stock Symbol" column
        for idx, row in df.iterrows():
            if row.iloc[0] and 'stock' in str(row.iloc[0]).strip().lower():
                return idx
    
    return 0


def extract_metadata(df: pd.DataFrame) -> Dict[str, str]:
    """
    Extract metadata from initial rows (Account, Name, etc.).
    
    Args:
        df: DataFrame with metadata rows
    
    Returns:
        Dictionary of metadata
    """
    metadata = {}
    
    for idx, row in df.iterrows():
        first_col = str(row.iloc[0]).strip() if row.iloc[0] else ""
        second_col = str(row.iloc[1]).strip() if len(row) > 1 and row.iloc[1] else ""
        
        if first_col.lower() == 'account':
            metadata['account'] = second_col
        elif first_col.lower() == 'name':
            metadata['name'] = second_col
        elif 'trade book' in first_col.lower():
            metadata['period'] = second_col
        elif 'capital gain' in first_col.lower():
            metadata['fiscal_year'] = second_col
        
        # Stop when we hit actual data columns
        if first_col.lower() in ['date', 'stock symbol']:
            break
    
    return metadata


def read_broker_file(file_path: str) -> Dict:
    """
    Read a broker export file and return structured data.
    Supports Excel (.xlsx, .xls) and CSV (.csv) files.
    
    Args:
        file_path: Path to broker file
    
    Returns:
        Dictionary with:
            - client_id: Client identifier
            - broker: Broker name
            - file_type: Type of file
            - metadata: Account info, name, period
            - data: DataFrame with the actual data
    """
    # Detect file type
    file_type = detect_file_type(file_path)
    if not file_type:
        raise ValueError(f"Could not determine file type for: {file_path}")
    
    # Extract client and broker from path
    client_id, broker = extract_client_broker_from_path(file_path)
    
    # Read file based on extension
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.csv':
        df = read_csv_file(file_path)
    else:
        # Read Excel with tab detection
        df = read_excel_with_tab_detection(file_path)
    
    # Extract metadata
    metadata = extract_metadata(df)
    
    # Find where data starts
    data_start = find_data_start_row(df, file_type)
    
    # Extract data portion
    if data_start >= 0:
        # Set column names from data_start row
        data_df = df.iloc[data_start:].copy()
        data_df.columns = data_df.iloc[0]
        data_df = data_df.iloc[1:].reset_index(drop=True)
        
        # Remove empty rows
        data_df = data_df.dropna(how='all')
    else:
        data_df = pd.DataFrame()
    
    return {
        'client_id': client_id,
        'broker': broker,
        'file_type': file_type,
        'metadata': metadata,
        'data': data_df,
        'file_path': file_path
    }


def discover_all_files(data_dir: str) -> List[str]:
    """
    Discover all Excel files in the data directory.
    
    Args:
        data_dir: Root data directory
    
    Returns:
        List of file paths
    """
    file_paths = []
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith(('.xlsx', '.xls', '.csv')):
                file_paths.append(os.path.join(root, file))
    
    return file_paths


def ingest_all_files(data_dir: str) -> List[Dict]:
    """
    Ingest all broker files from data directory.
    
    Args:
        data_dir: Root data directory
    
    Returns:
        List of ingested file data dictionaries
    """
    file_paths = discover_all_files(data_dir)
    
    ingested_data = []
    errors = []
    
    for file_path in file_paths:
        try:
            data = read_broker_file(file_path)
            ingested_data.append(data)
        except Exception as e:
            errors.append({
                'file_path': file_path,
                'error': str(e)
            })
    
    if errors:
        print(f"Warning: {len(errors)} files failed to ingest:")
        for err in errors[:5]:  # Show first 5 errors
            print(f"  {err['file_path']}: {err['error']}")
    
    print(f"Successfully ingested {len(ingested_data)} files")
    
    return ingested_data
