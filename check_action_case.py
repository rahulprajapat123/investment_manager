"""
Investigate the action column issue - case sensitivity problem.
"""
import pandas as pd
from pathlib import Path

project_root = Path(__file__).parent
reports_dir = project_root / "reports"
report_file = reports_dir / "C001_portfolio_report.xlsx"

print("\n" + "="*100)
print("INVESTIGATING ACTION COLUMN CASE SENSITIVITY ISSUE")
print("="*100 + "\n")

# Load Calculations sheet
calc_df = pd.read_excel(report_file, sheet_name='Calculations')

# Check action column unique values
print("Unique values in 'action' column:")
print(calc_df['action'].unique())
print(f"\nValue counts:")
print(calc_df['action'].value_counts())

# Check a specific row
print("\n\nDetailed look at row 0:")
row0 = calc_df.iloc[0]
print(f"Symbol: {row0['symbol']}")
print(f"Action: '{row0['action']}' (type: {type(row0['action'])})")
print(f"Qty: {row0['qty']} (type: {type(row0['qty'])})")

# Check if it's matching the string
print(f"\nAction == 'buy': {row0['action'] == 'buy'}")
print(f"Action == 'Buy': {row0['action'] == 'Buy'}")  
print(f"Action == 'Sell': {row0['action'] == 'Sell'}")
print(f"Action == 'sell': {row0['action'] == 'sell'}")

# Filter using both cases
buys_lower = calc_df[calc_df['action'] == 'buy']
buys_upper = calc_df[calc_df['action'] == 'Buy']
sells_lower = calc_df[calc_df['action'] == 'sell']
sells_upper = calc_df[calc_df['action'] == 'Sell']

print(f"\n\nFiltering results:")
print(f"action == 'buy': {len(buys_lower)} rows")
print(f"action == 'Buy': {len(buys_upper)} rows")
print(f"action == 'sell': {len(sells_lower)} rows")
print(f"action == 'Sell': {len(sells_upper)} rows")

# Now check TSLA with correct case
print("\n\nChecking TSLA with correct case:")
tsla_trades = calc_df[calc_df['symbol'] == 'TSLA']
print(f"Total TSLA trades: {len(tsla_trades)}")

tsla_buys = tsla_trades[tsla_trades['action'] == 'Buy']
tsla_sells = tsla_trades[tsla_trades['action'] == 'Sell']

print(f"\nTSLA Buys (action == 'Buy'): {len(tsla_buys)}")
if len(tsla_buys) > 0:
    print(f"  Buy quantities: {tsla_buys['qty'].tolist()}")
    print(f"  Total bought: {tsla_buys['qty'].sum():.2f}")

print(f"\nTSLA Sells (action == 'Sell'): {len(tsla_sells)}")
if len(tsla_sells) > 0:
    print(f"  Sell quantities: {tsla_sells['qty'].tolist()}")
    print(f"  Total sold: {tsla_sells['qty'].sum():.2f}")

print(f"\nNet position: {tsla_buys['qty'].sum() - tsla_sells['qty'].sum():.2f}")

print(f"\n{'='*100}\n")
