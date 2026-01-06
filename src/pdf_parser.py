"""
PDF parser module for extracting tables from broker PDF statements.
Supports various broker PDF formats.
"""
import pdfplumber
import pandas as pd
from typing import List, Dict, Optional
import re


def extract_tables_from_pdf(pdf_path: str) -> List[pd.DataFrame]:
    """
    Extract all tables from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        List of DataFrames, one for each table found
    """
    tables = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract tables from this page
                page_tables = page.extract_tables()
                
                if page_tables:
                    for table_num, table in enumerate(page_tables):
                        if table and len(table) > 0:
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            # Add metadata
                            df.attrs['page'] = page_num
                            df.attrs['table_num'] = table_num
                            tables.append(df)
                
                # Also try extracting text in case tables aren't detected
                if not page_tables:
                    text = page.extract_text()
                    if text:
                        # Try to parse text as table
                        df = parse_text_as_table(text)
                        if df is not None and not df.empty:
                            df.attrs['page'] = page_num
                            df.attrs['source'] = 'text_parsing'
                            tables.append(df)
    
    except Exception as e:
        print(f"Error extracting tables from PDF: {e}")
        raise
    
    return tables


def parse_text_as_table(text: str) -> Optional[pd.DataFrame]:
    """
    Try to parse text content as a table when table extraction fails.
    Looks for common patterns in broker statements.
    
    Args:
        text: Extracted text from PDF page
    
    Returns:
        DataFrame if table-like structure found, None otherwise
    """
    lines = text.split('\n')
    
    # Look for lines that might be table rows (contain multiple columns)
    potential_rows = []
    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue
        
        # Check if line has multiple space-separated or tab-separated values
        # Common patterns: date, symbol, quantity, price, etc.
        parts = re.split(r'\s{2,}|\t+', line.strip())
        
        if len(parts) >= 3:  # At least 3 columns to be a table
            potential_rows.append(parts)
    
    if len(potential_rows) > 2:  # At least header + 2 data rows
        # Use first row as header
        df = pd.DataFrame(potential_rows[1:], columns=potential_rows[0])
        return df
    
    return None


def find_largest_table(tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Find the table with the most rows (likely the main data table).
    
    Args:
        tables: List of DataFrames
    
    Returns:
        DataFrame with most rows
    """
    if not tables:
        return None
    
    return max(tables, key=lambda df: len(df))


def clean_pdf_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean extracted PDF table data.
    - Remove empty rows/columns
    - Strip whitespace
    - Handle merged cells
    
    Args:
        df: Raw DataFrame from PDF
    
    Returns:
        Cleaned DataFrame
    """
    # Remove completely empty rows and columns
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Strip whitespace from all string values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip() if hasattr(df[col], 'str') else df[col]
    
    # Replace empty strings with NaN
    df = df.replace('', pd.NA)
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df


def extract_metadata_from_pdf(pdf_path: str) -> Dict[str, str]:
    """
    Extract metadata from PDF (account number, date range, client name, etc.)
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Dictionary with extracted metadata
    """
    metadata = {}
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from first page (usually contains header info)
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            if text:
                # Look for common patterns
                
                # Account number patterns
                account_patterns = [
                    r'Account\s*(?:No|Number|#)[:\s]*([A-Z0-9\-]+)',
                    r'A/C\s*(?:No|Number)[:\s]*([A-Z0-9\-]+)',
                    r'Client\s*(?:ID|Code)[:\s]*([A-Z0-9\-]+)'
                ]
                for pattern in account_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        metadata['account_number'] = match.group(1).strip()
                        break
                
                # Date range patterns
                date_patterns = [
                    r'Period[:\s]*([\d/\-]+)\s*(?:to|–|-)\s*([\d/\-]+)',
                    r'From[:\s]*([\d/\-]+)\s*(?:To|to)[:\s]*([\d/\-]+)',
                    r'Statement\s*Period[:\s]*([\d/\-]+)\s*(?:to|–|-)\s*([\d/\-]+)'
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        metadata['start_date'] = match.group(1).strip()
                        metadata['end_date'] = match.group(2).strip()
                        break
                
                # Client name patterns
                name_patterns = [
                    r'Name[:\s]*([A-Za-z\s\.]+?)(?:\n|Account|Client)',
                    r'Client\s*Name[:\s]*([A-Za-z\s\.]+?)(?:\n|$)'
                ]
                for pattern in name_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        metadata['client_name'] = match.group(1).strip()
                        break
    
    except Exception as e:
        print(f"Error extracting metadata from PDF: {e}")
    
    return metadata


def read_pdf_broker_file(pdf_path: str) -> pd.DataFrame:
    """
    Main function to read a broker PDF file and extract the primary data table.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        DataFrame with the main data table
    """
    # Extract all tables
    tables = extract_tables_from_pdf(pdf_path)
    
    if not tables:
        raise ValueError(f"No tables found in PDF: {pdf_path}")
    
    # Get the largest table (usually the main data)
    main_table = find_largest_table(tables)
    
    if main_table is None:
        raise ValueError(f"Could not extract data table from PDF: {pdf_path}")
    
    # Clean the table
    main_table = clean_pdf_table(main_table)
    
    return main_table
