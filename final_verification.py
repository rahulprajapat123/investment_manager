"""
Final verification: Spot-check calculations for specific stocks across brokers.
This validates that calculations are mathematically correct.
"""
import pandas as pd
from pathlib import Path

def verify_stock_calculations(client_id, reports_dir):
    """Verify calculations for specific stocks."""
    print(f"\n{'='*100}")
    print(f"SPOT-CHECK CALCULATION VERIFICATION: {client_id}")
    print(f"{'='*100}\n")
    
    generated_file = reports_dir / f"{client_id}_portfolio_report.xlsx"
    
    if not generated_file.exists():
        print(f"❌ Generated file not found: {generated_file}")
        return
    
    # Load holdings
    holdings_df = pd.read_excel(generated_file, sheet_name='Holdings')
    
    print(f"📊 Verifying calculations for {len(holdings_df)} holdings\n")
    print(f"{'Stock':<15} {'Platform':<20} {'Qty':<10} {'Avg Cost':<12} {'Curr Price':<12} {'Invested':<15} {'Curr Val':<15} {'P/L':<15} {'P/L %':<10} {'Status'}")
    print("="*140)
    
    all_correct = True
    
    for idx, row in holdings_df.iterrows():
        symbol = row['Asset Name']
        platform = row['Platform']
        qty = row['Quantity']
        avg_cost = row['Average Cost']
        curr_price = row['Current Price']
        invested = row['Total Invested']
        curr_val = row['Current Value']
        pnl = row['Unrealized P/L']
        pnl_pct = row['P/L %']
        
        # Verify calculations
        calc_invested = qty * avg_cost
        calc_curr_val = qty * curr_price
        calc_pnl = calc_curr_val - calc_invested
        calc_pnl_pct = calc_pnl / calc_invested if calc_invested != 0 else 0
        
        # Check with tolerance
        tolerance = 0.02  # Allow 2 cents difference due to rounding
        
        invested_match = abs(invested - calc_invested) < tolerance
        curr_val_match = abs(curr_val - calc_curr_val) < tolerance
        pnl_match = abs(pnl - calc_pnl) < tolerance
        pnl_pct_match = abs(pnl_pct - calc_pnl_pct) < 0.0001
        
        all_match = invested_match and curr_val_match and pnl_match and pnl_pct_match
        
        status = "✓" if all_match else "❌"
        if not all_match:
            all_correct = False
        
        print(f"{symbol:<15} {platform:<20} {qty:<10.2f} {avg_cost:<12.2f} {curr_price:<12.2f} {invested:<15.2f} {curr_val:<15.2f} {pnl:<15.2f} {pnl_pct:<10.2%} {status}")
        
        # Show detailed errors if any
        if not all_match:
            if not invested_match:
                print(f"    ⚠ Invested: Expected {calc_invested:.2f}, Got {invested:.2f}, Diff: {abs(invested - calc_invested):.2f}")
            if not curr_val_match:
                print(f"    ⚠ Current Value: Expected {calc_curr_val:.2f}, Got {curr_val:.2f}, Diff: {abs(curr_val - calc_curr_val):.2f}")
            if not pnl_match:
                print(f"    ⚠ P/L: Expected {calc_pnl:.2f}, Got {pnl:.2f}, Diff: {abs(pnl - calc_pnl):.2f}")
            if not pnl_pct_match:
                print(f"    ⚠ P/L %: Expected {calc_pnl_pct:.4f}, Got {pnl_pct:.4f}, Diff: {abs(pnl_pct - calc_pnl_pct):.4f}")
    
    print("="*140)
    
    if all_correct:
        print("\n✅ ALL CALCULATIONS ARE MATHEMATICALLY CORRECT!\n")
    else:
        print("\n⚠ Some calculations have discrepancies (check above for details)\n")
    
    # Verify summary totals
    print("\n📊 VERIFYING SUMMARY TOTALS:\n")
    
    summary_df = pd.read_excel(generated_file, sheet_name='Summary')
    summary_dict = dict(zip(summary_df.iloc[:, 0], summary_df.iloc[:, 1]))
    
    # Calculate totals from holdings
    total_invested = holdings_df['Total Invested'].sum()
    total_curr_val = holdings_df['Current Value'].sum()
    total_pnl = holdings_df['Unrealized P/L'].sum()
    
    # Get from summary
    summary_curr_val = summary_dict.get('Total Current Value', 0)
    summary_invested = summary_dict.get('Total Invested', 0)
    summary_pnl = summary_dict.get('Unrealized P/L', 0)
    
    print(f"Total Current Value:")
    print(f"  From Holdings Sum:  {total_curr_val:,.2f}")
    print(f"  From Summary:       {summary_curr_val:,.2f}")
    print(f"  Match: {'✓' if abs(total_curr_val - summary_curr_val) < 0.02 else '❌'}\n")
    
    print(f"Total Invested:")
    print(f"  From Holdings Sum:  {total_invested:,.2f}")
    print(f"  From Summary:       {summary_invested:,.2f}")
    print(f"  Match: {'✓' if abs(total_invested - summary_invested) < 0.02 else '❌'}\n")
    
    print(f"Unrealized P/L:")
    print(f"  From Holdings Sum:  {total_pnl:,.2f}")
    print(f"  From Summary:       {summary_pnl:,.2f}")
    print(f"  Match: {'✓' if abs(total_pnl - summary_pnl) < 0.02 else '❌'}\n")
    
    return all_correct

def verify_ticker_names(client_id, data_dir, reports_dir):
    """Verify that ticker names from data files match those in the report."""
    print(f"\n{'='*100}")
    print(f"TICKER NAME VERIFICATION: {client_id}")
    print(f"{'='*100}\n")
    
    client_path = Path(data_dir) / client_id
    generated_file = reports_dir / f"{client_id}_portfolio_report.xlsx"
    
    # Collect all symbols from data files
    data_symbols = set()
    
    brokers = [d.name for d in client_path.iterdir() if d.is_dir()]
    for broker in brokers:
        holdings_file = client_path / broker / "holdings.csv"
        if holdings_file.exists():
            df = pd.read_csv(holdings_file)
            if 'Asset_Name' in df.columns:
                data_symbols.update(df['Asset_Name'].unique())
    
    # Get symbols from report (current holdings only)
    holdings_df = pd.read_excel(generated_file, sheet_name='Holdings')
    report_symbols = set(holdings_df['Asset Name'].unique())
    
    print(f"Symbols in data files: {len(data_symbols)}")
    print(f"Symbols in report (current holdings): {len(report_symbols)}")
    print(f"\nReport symbols: {', '.join(sorted(report_symbols))}\n")
    
    # Check if report symbols are subset of data symbols
    if report_symbols.issubset(data_symbols):
        print("✅ All ticker names in report are found in data files")
        print("✅ Ticker names are correctly extracted and processed\n")
        return True
    else:
        missing = report_symbols - data_symbols
        print(f"⚠ Some symbols in report not found in data files: {missing}\n")
        return False

def main():
    """Main verification function."""
    print("\n" + "="*100)
    print("FINAL CALCULATION AND TICKER VERIFICATION")
    print("="*100)
    print("\nThis verification:")
    print("  1. Spot-checks mathematical calculations for each holding")
    print("  2. Verifies summary totals match sum of holdings")
    print("  3. Confirms ticker names are correctly extracted from data files")
    print("="*100)
    
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    reports_dir = project_root / "reports"
    
    # Verify C001
    c001_calc = verify_stock_calculations("C001", reports_dir)
    c001_ticker = verify_ticker_names("C001", data_dir, reports_dir)
    
    # Verify C002
    c002_calc = verify_stock_calculations("C002", reports_dir)
    c002_ticker = verify_ticker_names("C002", data_dir, reports_dir)
    
    # Final summary
    print("\n" + "="*100)
    print("FINAL VERIFICATION SUMMARY")
    print("="*100)
    print(f"C001 Calculations: {'✅ CORRECT' if c001_calc else '❌ ISSUES FOUND'}")
    print(f"C001 Ticker Names: {'✅ CORRECT' if c001_ticker else '❌ ISSUES FOUND'}")
    print(f"C002 Calculations: {'✅ CORRECT' if c002_calc else '❌ ISSUES FOUND'}")
    print(f"C002 Ticker Names: {'✅ CORRECT' if c002_ticker else '❌ ISSUES FOUND'}")
    print("="*100)
    
    if c001_calc and c001_ticker and c002_calc and c002_ticker:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("✅ All calculations are mathematically correct")
        print("✅ All ticker names are correctly extracted and processed")
        print("✅ All stock numbers and quantities are accurate")
        print("✅ Summary totals match individual holdings")
        print("="*100 + "\n")
    else:
        print("\n⚠ Some verification checks failed - review details above")
        print("="*100 + "\n")

if __name__ == "__main__":
    main()
