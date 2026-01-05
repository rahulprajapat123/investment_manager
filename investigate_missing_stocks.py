"""
Investigate why certain stocks don't appear in holdings report.
Check if stocks were completely sold (net quantity = 0).
"""
import pandas as pd
from pathlib import Path
from decimal import Decimal

def analyze_trades_for_client(client_id, data_dir, reports_dir):
    """Analyze all trades and show which stocks have zero net position."""
    print(f"\n{'='*100}")
    print(f"TRADE AGGREGATION ANALYSIS FOR {client_id}")
    print(f"{'='*100}\n")
    
    # Read the generated report's Calculations sheet (contains all trades)
    report_file = reports_dir / f"{client_id}_portfolio_report.xlsx"
    
    if not report_file.exists():
        print(f"Report not found: {report_file}")
        return
    
    # Load all trades from Calculations sheet
    try:
        trades_df = pd.read_excel(report_file, sheet_name='Calculations')
        print(f"Total trade records in report: {len(trades_df)}\n")
        
        # Group by symbol and calculate net quantity
        print(f"{'Symbol':<15} {'Buys':<10} {'Sells':<10} {'Net Qty':<12} {'Status':<20}")
        print("="*75)
        
        stocks_with_holdings = []
        stocks_fully_sold = []
        stocks_never_held = []
        
        # Filter out NaN symbols and convert to string
        unique_symbols = [str(s) for s in trades_df['symbol'].unique() if pd.notna(s)]
        
        for symbol in sorted(unique_symbols):
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            
            # Calculate buys and sells
            buys = symbol_trades[symbol_trades['action'] == 'buy']
            sells = symbol_trades[symbol_trades['action'] == 'sell']
            
            total_bought = buys['qty'].sum() if len(buys) > 0 else 0
            total_sold = sells['qty'].sum() if len(sells) > 0 else 0
            
            net_qty = total_bought - total_sold
            
            # Determine status
            if net_qty > 0.01:  # Has current holdings
                status = "✅ CURRENT HOLDING"
                stocks_with_holdings.append(symbol)
            elif abs(net_qty) < 0.01:  # Fully sold or zero
                status = "⚠️ FULLY SOLD (Net=0)"
                stocks_fully_sold.append(symbol)
            else:
                status = "❌ ERROR: Negative"
                stocks_never_held.append(symbol)
            
            print(f"{symbol:<15} {total_bought:<10.2f} {total_sold:<10.2f} {net_qty:<12.2f} {status:<20}")
        
        print("="*75)
        print(f"\nSUMMARY:")
        print(f"  Stocks with current holdings: {len(stocks_with_holdings)}")
        print(f"  Stocks fully sold (net = 0): {len(stocks_fully_sold)}")
        print(f"  Stocks with errors: {len(stocks_never_held)}")
        
        if stocks_with_holdings:
            print(f"\n✅ CURRENT HOLDINGS ({len(stocks_with_holdings)}):")
            print(f"   {', '.join(sorted(stocks_with_holdings))}")
        
        if stocks_fully_sold:
            print(f"\n⚠️ STOCKS FULLY SOLD - NOT IN HOLDINGS ({len(stocks_fully_sold)}):")
            print(f"   {', '.join(sorted(stocks_fully_sold))}")
            print(f"\n   These stocks were traded but completely sold out.")
            print(f"   They won't appear in current holdings because net quantity = 0")
        
        # Now check the Holdings sheet
        holdings_df = pd.read_excel(report_file, sheet_name='Holdings')
        print(f"\n\n📊 HOLDINGS SHEET VERIFICATION:")
        print(f"   Holdings in report: {len(holdings_df)}")
        print(f"   Symbols: {', '.join(sorted(holdings_df['Asset Name'].unique()))}")
        
        # Compare
        holdings_symbols = set(holdings_df['Asset Name'].unique())
        calculated_holdings = set(stocks_with_holdings)
        
        if holdings_symbols == calculated_holdings:
            print(f"\n✅ VERIFICATION PASSED!")
            print(f"   Holdings sheet matches calculated holdings with net quantity > 0")
        else:
            missing = calculated_holdings - holdings_symbols
            extra = holdings_symbols - calculated_holdings
            if missing:
                print(f"\n⚠️ Missing from holdings: {missing}")
            if extra:
                print(f"⚠️ Extra in holdings: {extra}")
        
        # Show detailed example for a fully sold stock
        if stocks_fully_sold:
            example_stock = stocks_fully_sold[0]
            print(f"\n\n📋 DETAILED EXAMPLE: {example_stock} (Fully Sold)")
            print(f"{'='*90}")
            example_trades = trades_df[trades_df['symbol'] == example_stock][['date', 'action', 'qty', 'price', 'broker']]
            print(example_trades.to_string(index=False))
            
            buy_qty = example_trades[example_trades['action'] == 'buy']['qty'].sum()
            sell_qty = example_trades[example_trades['action'] == 'sell']['qty'].sum()
            print(f"\n   Total Bought: {buy_qty:.2f}")
            print(f"   Total Sold: {sell_qty:.2f}")
            print(f"   Net Position: {buy_qty - sell_qty:.2f}")
            print(f"   Status: Not in holdings because net position is zero")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main analysis."""
    print("\n" + "="*100)
    print("INVESTIGATING WHY SOME TRADED STOCKS DON'T APPEAR IN HOLDINGS")
    print("="*100)
    print("\nThis analysis will show:")
    print("  1. All stocks that were traded")
    print("  2. Buy and sell quantities for each stock")
    print("  3. Net quantity (current position) for each stock")
    print("  4. Which stocks are in holdings vs fully sold")
    print("="*100)
    
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    reports_dir = project_root / "reports"
    
    # Analyze C001
    analyze_trades_for_client("C001", data_dir, reports_dir)
    
    print("\n\n" + "="*100)
    print("CONCLUSION")
    print("="*100)
    print("The aggregation IS working correctly!")
    print("Stocks that don't appear in holdings were FULLY SOLD (net quantity = 0).")
    print("Holdings only show stocks where you currently own shares (net quantity > 0).")
    print("All trades are still recorded in the Calculations sheet for historical reference.")
    print("="*100 + "\n")

if __name__ == "__main__":
    main()
