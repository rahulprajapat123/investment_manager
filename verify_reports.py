"""
Comprehensive verification script to compare generated reports with original portfolio files.
Checks calculations, stock numbers, ticker names, and all metrics.
"""
import pandas as pd
import openpyxl
from pathlib import Path
from decimal import Decimal
import sys

def load_excel_sheets(file_path):
    """Load all sheets from an Excel file."""
    try:
        xl = pd.ExcelFile(file_path)
        sheets = {}
        for sheet_name in xl.sheet_names:
            sheets[sheet_name] = pd.read_excel(file_path, sheet_name=sheet_name)
        return sheets
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def compare_dataframes(df1, df2, sheet_name, tolerance=0.01):
    """Compare two dataframes and report differences."""
    differences = []
    
    if df1 is None or df2 is None:
        return ["One or both dataframes are None"]
    
    # Check shape
    if df1.shape != df2.shape:
        differences.append(f"Shape mismatch: Original {df1.shape} vs Generated {df2.shape}")
    
    # Check column names
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    if cols1 != cols2:
        missing_in_generated = cols1 - cols2
        extra_in_generated = cols2 - cols1
        if missing_in_generated:
            differences.append(f"Columns missing in generated: {missing_in_generated}")
        if extra_in_generated:
            differences.append(f"Extra columns in generated: {extra_in_generated}")
    
    # For numeric comparisons
    common_cols = cols1.intersection(cols2)
    
    for col in common_cols:
        if col in df1.columns and col in df2.columns:
            # Check if column is numeric
            if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col]):
                # Compare numeric values with tolerance
                try:
                    diff = (df1[col] - df2[col]).abs()
                    if (diff > tolerance).any():
                        max_diff = diff.max()
                        differences.append(f"Column '{col}' has numeric differences (max: {max_diff:.4f})")
                except Exception as e:
                    differences.append(f"Error comparing column '{col}': {e}")
            else:
                # Compare non-numeric values
                try:
                    if not df1[col].equals(df2[col]):
                        mismatches = (df1[col] != df2[col]).sum()
                        differences.append(f"Column '{col}' has {mismatches} mismatched values")
                except Exception as e:
                    differences.append(f"Error comparing column '{col}': {e}")
    
    return differences

def verify_client(client_id, reports_dir):
    """Verify a specific client's report."""
    print(f"\n{'='*80}")
    print(f"VERIFYING CLIENT: {client_id}")
    print(f"{'='*80}\n")
    
    # File paths
    original_file = reports_dir / f"{client_id}_portfolio (2).xlsx" if client_id == "C001" else reports_dir / f"{client_id}_portfolio (1).xlsx"
    generated_file = reports_dir / f"{client_id}_portfolio_report.xlsx"
    
    if not original_file.exists():
        print(f"❌ Original file not found: {original_file}")
        return False
    
    if not generated_file.exists():
        print(f"❌ Generated file not found: {generated_file}")
        return False
    
    print(f"Original:  {original_file.name}")
    print(f"Generated: {generated_file.name}\n")
    
    # Load both files
    print("Loading Excel files...")
    original_sheets = load_excel_sheets(original_file)
    generated_sheets = load_excel_sheets(generated_file)
    
    if original_sheets is None or generated_sheets is None:
        print("❌ Failed to load files")
        return False
    
    print(f"✓ Original file has {len(original_sheets)} sheets: {list(original_sheets.keys())}")
    print(f"✓ Generated file has {len(generated_sheets)} sheets: {list(generated_sheets.keys())}\n")
    
    # Compare each sheet
    all_match = True
    
    for sheet_name in original_sheets.keys():
        print(f"\n--- Comparing Sheet: {sheet_name} ---")
        
        if sheet_name not in generated_sheets:
            print(f"❌ Sheet '{sheet_name}' not found in generated report")
            all_match = False
            continue
        
        original_df = original_sheets[sheet_name]
        generated_df = generated_sheets[sheet_name]
        
        print(f"Original shape: {original_df.shape}")
        print(f"Generated shape: {generated_df.shape}")
        
        differences = compare_dataframes(original_df, generated_df, sheet_name)
        
        if not differences:
            print(f"✓ Sheet '{sheet_name}' matches perfectly!")
        else:
            print(f"⚠ Sheet '{sheet_name}' has differences:")
            for diff in differences:
                print(f"  - {diff}")
            all_match = False
        
        # Show sample data for key sheets
        if sheet_name in ['Summary', 'Holdings', 'Trades']:
            print(f"\nSample from Original '{sheet_name}':")
            print(original_df.head(3).to_string())
            print(f"\nSample from Generated '{sheet_name}':")
            print(generated_df.head(3).to_string())
    
    # Check for extra sheets in generated
    extra_sheets = set(generated_sheets.keys()) - set(original_sheets.keys())
    if extra_sheets:
        print(f"\n⚠ Extra sheets in generated report: {extra_sheets}")
    
    return all_match

def detailed_stock_verification(client_id, reports_dir):
    """Perform detailed verification of stock data."""
    print(f"\n{'='*80}")
    print(f"DETAILED STOCK VERIFICATION: {client_id}")
    print(f"{'='*80}\n")
    
    original_file = reports_dir / f"{client_id}_portfolio (2).xlsx" if client_id == "C001" else reports_dir / f"{client_id}_portfolio (1).xlsx"
    generated_file = reports_dir / f"{client_id}_portfolio_report.xlsx"
    
    # Load holdings/summary sheets
    try:
        original_summary = pd.read_excel(original_file, sheet_name='Summary')
        generated_summary = pd.read_excel(generated_file, sheet_name='Summary')
        
        print("SUMMARY SHEET COMPARISON:")
        print("\nOriginal Summary:")
        print(original_summary.to_string())
        print("\nGenerated Summary:")
        print(generated_summary.to_string())
        
    except Exception as e:
        print(f"Error loading summary sheets: {e}")
    
    # Load holdings if available
    try:
        original_holdings = pd.read_excel(original_file, sheet_name='Holdings')
        generated_holdings = pd.read_excel(generated_file, sheet_name='Holdings')
        
        print("\n\nHOLDINGS COMPARISON:")
        print(f"\nOriginal Holdings ({len(original_holdings)} rows):")
        print(original_holdings.to_string())
        print(f"\nGenerated Holdings ({len(generated_holdings)} rows):")
        print(generated_holdings.to_string())
        
        # Compare specific metrics
        if 'Symbol' in original_holdings.columns and 'Symbol' in generated_holdings.columns:
            orig_symbols = set(original_holdings['Symbol'].dropna().unique())
            gen_symbols = set(generated_holdings['Symbol'].dropna().unique())
            
            print(f"\n\nSTOCK SYMBOLS:")
            print(f"Original symbols ({len(orig_symbols)}): {sorted(orig_symbols)}")
            print(f"Generated symbols ({len(gen_symbols)}): {sorted(gen_symbols)}")
            
            if orig_symbols == gen_symbols:
                print("✓ All stock symbols match!")
            else:
                missing = orig_symbols - gen_symbols
                extra = gen_symbols - orig_symbols
                if missing:
                    print(f"❌ Missing symbols in generated: {missing}")
                if extra:
                    print(f"⚠ Extra symbols in generated: {extra}")
        
    except Exception as e:
        print(f"Error loading holdings sheets: {e}")
    
    # Load trades
    try:
        original_trades = pd.read_excel(original_file, sheet_name='Trades')
        generated_trades = pd.read_excel(generated_file, sheet_name='Trades')
        
        print(f"\n\nTRADES COMPARISON:")
        print(f"Original trades: {len(original_trades)} records")
        print(f"Generated trades: {len(generated_trades)} records")
        
        if len(original_trades) != len(generated_trades):
            print(f"⚠ Trade count mismatch!")
        else:
            print(f"✓ Trade counts match!")
        
    except Exception as e:
        print(f"Error loading trades sheets: {e}")

def main():
    """Main verification function."""
    print("\n" + "="*80)
    print("COMPREHENSIVE PORTFOLIO VERIFICATION")
    print("="*80)
    
    reports_dir = Path(__file__).parent / "reports"
    
    if not reports_dir.exists():
        print(f"❌ Reports directory not found: {reports_dir}")
        return
    
    # Verify C001
    c001_match = verify_client("C001", reports_dir)
    detailed_stock_verification("C001", reports_dir)
    
    # Verify C002
    c002_match = verify_client("C002", reports_dir)
    detailed_stock_verification("C002", reports_dir)
    
    # Final summary
    print(f"\n\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*80}")
    print(f"C001: {'✓ PASSED' if c001_match else '❌ DIFFERENCES FOUND'}")
    print(f"C002: {'✓ PASSED' if c002_match else '❌ DIFFERENCES FOUND'}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
