"""
Check the actual Calculations sheet to see what trades are in the report.
"""
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
reports_dir = project_root / "reports"
report_file = reports_dir / "C001_portfolio_report.xlsx"

print("\n" + "="*100)
print("CHECKING C001 CALCULATIONS SHEET - RAW TRADE DATA")
print("="*100 + "\n")

# Load Calculations sheet
calc_df = pd.read_excel(report_file, sheet_name='Calculations')

print(f"Total rows in Calculations: {len(calc_df)}")
print(f"Columns: {list(calc_df.columns)}\n")

# Show first 20 rows
print("First 20 trades:")
print("="*120)
print(calc_df.head(20).to_string())

# Filter for Charles_Schwab trades
cs_trades = calc_df[calc_df['broker'] == 'Charles_Schwab']
print(f"\n\nCharles_Schwab trades: {len(cs_trades)}")

# Show unique symbols from Charles_Schwab
cs_symbols = cs_trades['symbol'].unique()
print(f"Unique symbols in Charles_Schwab: {len(cs_symbols)}")
#print(f"Symbols: {sorted([str(s) for s in cs_symbols if pd.notna(s)])[:20]}")

# Check for TSLA, AAPL, AMZN specifically
print(f"\n\nChecking for specific stocks in Charles_Schwab:")
for stock in ['TSLA', 'AAPL', 'AMZN', 'SPY', 'GOOGL', 'NVDA', 'JPM', 'META']:
    stock_trades = cs_trades[cs_trades['symbol'] == stock]
    if len(stock_trades) > 0:
        buys = stock_trades[stock_trades['action'] == 'buy']
        sells = stock_trades[stock_trades['action'] == 'sell']
        buy_qty = buys['qty'].sum() if len(buys) > 0 else 0
        sell_qty = sells['qty'].sum() if len(sells) > 0 else 0
        net = buy_qty - sell_qty
        print(f"  {stock}: {len(stock_trades)} trades, Bought={buy_qty:.2f}, Sold={sell_qty:.2f}, Net={net:.2f}")
    else:
        print(f"  {stock}: NOT FOUND in calculations")

print(f"\n{'='*100}\n")
