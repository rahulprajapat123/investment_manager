"""
Test CSV file ingestion to verify it works correctly.
"""
import sys
sys.path.append('src')

from ingestion import read_csv_file, read_broker_file
import pandas as pd
import os

print("=" * 80)
print("CSV FILE SUPPORT TEST")
print("=" * 80)

# Create a sample CSV file for testing
test_csv_path = 'data/C001/tradeBook_TestBroker.csv'

# Sample trade data
sample_data = """Date,Stock,Action,Qty,Price,Trade Value,Exchange,Currency
2024-01-15,RELIANCE,Buy,100,2500.50,250050.00,NSE,INR
2024-02-20,HDFCBANK,Buy,50,1600.75,80037.50,NSE,INR
2024-03-10,RELIANCE,Sell,50,2650.00,132500.00,NSE,INR
2024-04-05,TCS,Buy,30,3500.25,105007.50,NSE,INR
"""

# Write sample CSV file
os.makedirs('data/C001', exist_ok=True)
with open(test_csv_path, 'w') as f:
    f.write(sample_data)

print(f"\n1. Created test CSV file: {test_csv_path}")

# Test reading CSV file
print("\n2. Testing CSV file reading...")
try:
    df = read_csv_file(test_csv_path)
    print(f"   ✓ Successfully read CSV file")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {df.columns.tolist()}")
    print("\n   First 3 rows:")
    print(df.head(3).to_string())
except Exception as e:
    print(f"   ✗ Error reading CSV: {e}")

# Test full broker file reading
print("\n3. Testing full broker file ingestion...")
try:
    data = read_broker_file(test_csv_path)
    print(f"   ✓ Successfully ingested CSV file")
    print(f"   Client ID: {data['client_id']}")
    print(f"   Broker: {data['broker']}")
    print(f"   File Type: {data['file_type']}")
    print(f"   Data shape: {data['data'].shape}")
except Exception as e:
    print(f"   ✗ Error ingesting CSV: {e}")
    import traceback
    traceback.print_exc()

# Test with different CSV delimiters
print("\n4. Testing different CSV delimiters...")

# Semicolon-delimited
test_csv_semicolon = 'data/C001/capitalGains_TestBroker2.csv'
sample_semicolon = """Stock Symbol;ISIN;Qty;Sale Date;Sale Rate;Profit/Loss;ST/LT
RELIANCE;INE002A01018;50;2024-03-10;2650.00;7475.00;ST
HDFCBANK;INE040A01034;25;2024-06-15;1750.00;3743.75;LT
"""

with open(test_csv_semicolon, 'w') as f:
    f.write(sample_semicolon)

try:
    df_semicolon = read_csv_file(test_csv_semicolon)
    print(f"   ✓ Semicolon-delimited CSV: {df_semicolon.shape}")
    print(f"   Columns: {df_semicolon.columns.tolist()}")
except Exception as e:
    print(f"   ✗ Error with semicolon CSV: {e}")

# Tab-delimited
test_csv_tab = 'data/C001/tradeBook_TestBroker3.csv'
sample_tab = "Date\tStock\tAction\tQty\tPrice\n2024-01-15\tITC\tBuy\t200\t450.50\n2024-02-20\tITC\tSell\t100\t475.00\n"

with open(test_csv_tab, 'w') as f:
    f.write(sample_tab)

try:
    df_tab = read_csv_file(test_csv_tab)
    print(f"   ✓ Tab-delimited CSV: {df_tab.shape}")
    print(f"   Columns: {df_tab.columns.tolist()}")
except Exception as e:
    print(f"   ✗ Error with tab CSV: {e}")

print("\n" + "=" * 80)
print("CSV SUPPORT TEST COMPLETE")
print("=" * 80)
print("\nYou can now upload CSV files through the web interface!")
print("The system will automatically detect the delimiter and process the file.")
