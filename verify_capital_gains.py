"""
Verify Capital Gains calculations as well.
"""
import sys
sys.path.append('src')

from ingestion import read_excel_with_tab_detection, find_data_start_row
import glob
import pandas as pd

def verify_capital_gains(stock_symbol, client='C001'):
    """Verify capital gains for a specific stock."""
    print("\n" + "=" * 80)
    print(f"CAPITAL GAINS VERIFICATION: {stock_symbol} FOR {client}")
    print("=" * 80)
    
    all_cg = []
    files = glob.glob(f'data\\{client}\\capitalGains_*.xlsx')
    
    for file in files:
        broker_name = file.split('_')[-1].replace('.xlsx', '')
        df = read_excel_with_tab_detection(file)
        data_start = find_data_start_row(df, 'capital_gains')
        
        if data_start is not None:
            df.columns = df.iloc[data_start]
            df = df.iloc[data_start + 1:]
            df = df.reset_index(drop=True)
            
            # Find symbol column
            col_name = None
            for col in df.columns:
                if col and ('stock' in str(col).lower() or 'symbol' in str(col).lower()):
                    col_name = col
                    break
            
            if col_name:
                df_stock = df[df[col_name] == stock_symbol]
                
                if not df_stock.empty:
                    # Find P&L column
                    pnl_col = None
                    for col in df.columns:
                        if col and ('profit' in str(col).lower() or 'loss' in str(col).lower()):
                            pnl_col = col
                            break
                    
                    if pnl_col:
                        for idx, row in df_stock.iterrows():
                            pnl = float(row[pnl_col]) if row[pnl_col] else 0
                            all_cg.append({
                                'broker': broker_name,
                                'pnl': pnl
                            })
    
    if all_cg:
        df_all = pd.DataFrame(all_cg)
        total_pnl = df_all['pnl'].sum()
        
        print(f"\nRAW DATA SUMMARY:")
        print(f"  Number of transactions: {len(all_cg)}")
        print(f"  Total P&L: {total_pnl:,.2f}")
        print(f"  Brokers with data: {df_all['broker'].unique().tolist()}")
        
        # Check report
        try:
            report = pd.read_excel(f'reports\\{client}_portfolio_report.xlsx', sheet_name='Calculations')
            
            # Capital gains section header is at row where client_id == 'client_id'
            cg_header_idx = None
            for idx in range(len(report)):
                if report.iloc[idx]['client_id'] == 'client_id':
                    cg_header_idx = idx
                    break
            
            if cg_header_idx is not None:
                # Capital gains data starts after the header row
                # The actual column mapping in CG section:
                # 'date' column contains 'symbol'
                # 'Unnamed: 14' contains 'pnl'
                report_cg = report.iloc[cg_header_idx + 1:].copy()
                
                # Get symbol from 'date' column and pnl from 'Unnamed: 14'
                report_stock = report_cg[report_cg['date'] == stock_symbol]
                
                if len(report_stock) > 0:
                    report_pnl = report_stock['Unnamed: 14'].astype(float).sum()
                    report_count = len(report_stock)
                    
                    print(f"\nREPORT SUMMARY:")
                    print(f"  Number of transactions: {report_count}")
                    print(f"  Total P&L: {report_pnl:,.2f}")
                    
                    print(f"\nMATCH STATUS:")
                    count_match = len(all_cg) == report_count
                    pnl_match = abs(total_pnl - report_pnl) < 1.0  # Allow small rounding difference
                    
                    print(f"  Transaction Count Match: {'✓ YES' if count_match else '✗ NO'}")
                    print(f"  P&L Match: {'✓ YES' if pnl_match else '✗ NO'}")
                    
                    if count_match and pnl_match:
                        print(f"\n✓ CAPITAL GAINS CALCULATIONS CORRECT FOR {stock_symbol}")
                    else:
                        print(f"\n✗ MISMATCH FOUND FOR {stock_symbol}")
                        if not count_match:
                            print(f"    Expected {len(all_cg)} transactions, got {report_count}")
                        if not pnl_match:
                            print(f"    Expected P&L {total_pnl:,.2f}, got {report_pnl:,.2f}")
                else:
                    print(f"\n✗ {stock_symbol} NOT FOUND IN CAPITAL GAINS REPORT")
            else:
                print("\nCould not locate capital gains section in report")
        except Exception as e:
            print(f"\nError reading report: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\nNo capital gains found for {stock_symbol} in raw data")

# Test a few stocks
print("=" * 80)
print("CAPITAL GAINS VERIFICATION")
print("=" * 80)

test_stocks = ['HDFCBANK', 'RELIANCE', 'ITC']

for stock in test_stocks:
    verify_capital_gains(stock)

print("\n" + "=" * 80)
print("CAPITAL GAINS VERIFICATION COMPLETE")
print("=" * 80)
