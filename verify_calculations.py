"""
Script to verify the calculations manually against raw data.
"""
import sys
sys.path.append('src')

from ingestion import read_excel_with_tab_detection, find_data_start_row
import glob
import pandas as pd
from decimal import Decimal

# Get all trade books for C001
print("=" * 80)
print("CHECKING MARUTI TRADES FOR C001")
print("=" * 80)

all_maruti_trades = []
files = glob.glob(r'data\C001\tradeBook_*.xlsx')

for file in files:
    broker_name = file.split('_')[-1].replace('.xlsx', '')
    print(f"\n{broker_name}:")
    print("-" * 40)
    
    df = read_excel_with_tab_detection(file)
    
    # Find where actual data starts
    data_start = find_data_start_row(df, 'trade_book')
    
    if data_start is not None:
        # Set column names from the header row
        df.columns = df.iloc[data_start]
        df = df.iloc[data_start + 1:]
        df = df.reset_index(drop=True)
        
        # Get the column names
        col_name = None
        for col in df.columns:
            if col and ('stock' in str(col).lower() or 'symbol' in str(col).lower()):
                col_name = col
                break
        
        if col_name:
            df_maruti = df[df[col_name] == 'MARUTI']
            
            if not df_maruti.empty:
                print(f"Found {len(df_maruti)} MARUTI trades")
                
                # Extract relevant columns
                for idx, row in df_maruti.iterrows():
                    action_col = [c for c in df.columns if c and 'action' in str(c).lower()]
                    qty_col = [c for c in df.columns if c and 'qty' in str(c).lower() or 'quantity' in str(c).lower()]
                    price_col = [c for c in df.columns if c and 'price' in str(c).lower()]
                    date_col = [c for c in df.columns if c and 'date' in str(c).lower()]
                    
                    if action_col and qty_col and price_col:
                        date_val = row[date_col[0]] if date_col else ''
                        action = row[action_col[0]]
                        qty = row[qty_col[0]]
                        price = row[price_col[0]]
                        print(f"  {date_val}: {action} {qty} @ {price}")
                        all_maruti_trades.append({
                            'broker': broker_name,
                            'date': date_val,
                            'action': action,
                            'qty': float(qty) if qty else 0,
                            'price': float(price) if price else 0
                        })
            else:
                print("No MARUTI trades found")
        else:
            print("Could not find stock column")
    else:
        print("Could not find data start row")

print("\n" + "=" * 80)
print("SUMMARY OF ALL MARUTI TRADES")
print("=" * 80)

if all_maruti_trades:
    df_all = pd.DataFrame(all_maruti_trades)
    print(f"\nTotal trades: {len(df_all)}")
    
    buy_trades = df_all[df_all['action'] == 'Buy']
    sell_trades = df_all[df_all['action'] == 'Sell']
    
    print(f"Buy trades: {len(buy_trades)}")
    print(f"Sell trades: {len(sell_trades)}")
    
    total_buy_qty = buy_trades['qty'].sum()
    total_sell_qty = sell_trades['qty'].sum()
    
    print(f"\nTotal Buy Quantity: {total_buy_qty}")
    print(f"Total Sell Quantity: {total_sell_qty}")
    print(f"Net Position: {total_buy_qty - total_sell_qty}")
    
    # Calculate weighted average buy price
    buy_trades['value'] = buy_trades['qty'] * buy_trades['price']
    total_buy_value = buy_trades['value'].sum()
    weighted_avg = total_buy_value / total_buy_qty if total_buy_qty > 0 else 0
    
    print(f"\nTotal Buy Value: {total_buy_value:.2f}")
    print(f"Weighted Average Buy Price: {weighted_avg:.2f}")
    
    print("\nDetailed Buy Trades:")
    print(buy_trades[['broker', 'date', 'qty', 'price', 'value']].to_string())

print("\n" + "=" * 80)
print("CHECKING WHAT THE SYSTEM GENERATED")
print("=" * 80)

# Check what's in the generated report
report = pd.read_excel(r'reports\C001_portfolio_report.xlsx', sheet_name='Calculations')
report_maruti = report[report['symbol'] == 'MARUTI'].iloc[:50]  # Get MARUTI trades

print("\nMARUTI trades from generated report:")
print(f"Total MARUTI trades in report: {len(report_maruti)}")
if len(report_maruti) > 0:
    print(report_maruti[['date', 'action', 'qty', 'price', 'trade_value']].to_string())
    
    buy_total = report_maruti[report_maruti['action'] == 'Buy']['qty'].sum()
    sell_total = report_maruti[report_maruti['action'] == 'Sell']['qty'].sum()
    
    print(f"\nReport Buy Total: {buy_total}")
    print(f"Report Sell Total: {sell_total}")
    print(f"Report Net Position: {buy_total - sell_total}")
else:
    print("No MARUTI trades found in report!")
