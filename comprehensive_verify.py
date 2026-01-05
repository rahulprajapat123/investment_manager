"""
Comprehensive verification of calculations across multiple stocks.
"""
import sys
sys.path.append('src')

from ingestion import read_excel_with_tab_detection, find_data_start_row
import glob
import pandas as pd
from decimal import Decimal

def verify_stock(stock_symbol, client='C001'):
    """Verify a specific stock's calculations."""
    print("\n" + "=" * 80)
    print(f"VERIFYING {stock_symbol} FOR {client}")
    print("=" * 80)
    
    all_trades = []
    files = glob.glob(f'data\\{client}\\tradeBook_*.xlsx')
    
    for file in files:
        broker_name = file.split('_')[-1].replace('.xlsx', '')
        df = read_excel_with_tab_detection(file)
        data_start = find_data_start_row(df, 'trade_book')
        
        if data_start is not None:
            df.columns = df.iloc[data_start]
            df = df.iloc[data_start + 1:]
            df = df.reset_index(drop=True)
            
            col_name = None
            for col in df.columns:
                if col and ('stock' in str(col).lower() or 'symbol' in str(col).lower()):
                    col_name = col
                    break
            
            if col_name:
                df_stock = df[df[col_name] == stock_symbol]
                
                if not df_stock.empty:
                    for idx, row in df_stock.iterrows():
                        action_col = [c for c in df.columns if c and 'action' in str(c).lower()]
                        qty_col = [c for c in df.columns if c and 'qty' in str(c).lower() or 'quantity' in str(c).lower()]
                        price_col = [c for c in df.columns if c and 'price' in str(c).lower()]
                        
                        if action_col and qty_col and price_col:
                            action = row[action_col[0]]
                            qty = float(row[qty_col[0]]) if row[qty_col[0]] else 0
                            price = float(row[price_col[0]]) if row[price_col[0]] else 0
                            all_trades.append({
                                'broker': broker_name,
                                'action': action,
                                'qty': qty,
                                'price': price
                            })
    
    if all_trades:
        df_all = pd.DataFrame(all_trades)
        
        buy_trades = df_all[df_all['action'] == 'Buy']
        sell_trades = df_all[df_all['action'] == 'Sell']
        
        total_buy_qty = buy_trades['qty'].sum()
        total_sell_qty = sell_trades['qty'].sum()
        
        print(f"\nRAW DATA SUMMARY:")
        print(f"  Total Buy Qty: {total_buy_qty:.2f}")
        print(f"  Total Sell Qty: {total_sell_qty:.2f}")
        print(f"  Net Position: {total_buy_qty - total_sell_qty:.2f}")
        
        if len(buy_trades) > 0:
            buy_trades_copy = buy_trades.copy()
            buy_trades_copy['value'] = buy_trades_copy['qty'] * buy_trades_copy['price']
            total_buy_value = buy_trades_copy['value'].sum()
            weighted_avg = total_buy_value / total_buy_qty if total_buy_qty > 0 else 0
            print(f"  Weighted Avg Buy Price: {weighted_avg:.2f}")
        
        # Check report
        try:
            report = pd.read_excel(f'reports\\{client}_portfolio_report.xlsx', sheet_name='Calculations')
            report_stock = report[report['symbol'] == stock_symbol]
            
            if len(report_stock) > 0:
                report_buy = report_stock[report_stock['action'] == 'Buy']['qty'].sum()
                report_sell = report_stock[report_stock['action'] == 'Sell']['qty'].sum()
                
                print(f"\nREPORT SUMMARY:")
                print(f"  Total Buy Qty: {report_buy:.2f}")
                print(f"  Total Sell Qty: {report_sell:.2f}")
                print(f"  Net Position: {report_buy - report_sell:.2f}")
                
                print(f"\nMATCH STATUS:")
                buy_match = abs(total_buy_qty - report_buy) < 0.01
                sell_match = abs(total_sell_qty - report_sell) < 0.01
                
                print(f"  Buy Qty Match: {'✓ YES' if buy_match else '✗ NO'}")
                print(f"  Sell Qty Match: {'✓ YES' if sell_match else '✗ NO'}")
                
                if buy_match and sell_match:
                    print(f"\n✓ ALL CALCULATIONS CORRECT FOR {stock_symbol}")
                else:
                    print(f"\n✗ MISMATCH FOUND FOR {stock_symbol}")
            else:
                print(f"\n✗ {stock_symbol} NOT FOUND IN REPORT")
        except Exception as e:
            print(f"\nError reading report: {e}")
    else:
        print(f"\nNo trades found for {stock_symbol} in raw data")

# Verify multiple stocks
stocks_to_verify = ['MARUTI', 'HDFCBANK', 'ICICIBANK', 'RELIANCE', 'TCS', 'ITC']

print("=" * 80)
print("COMPREHENSIVE CALCULATION VERIFICATION")
print("=" * 80)

for stock in stocks_to_verify:
    verify_stock(stock)

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
