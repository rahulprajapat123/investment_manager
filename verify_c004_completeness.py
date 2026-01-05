"""
Comprehensive verification script for C004 to check aggregation accuracy and stock completeness.
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pandas as pd
from ingestion import ingest_all_files
from normalizer import normalize_all_files
from report_generator import compute_current_holdings
from decimal_utils import sum_decimals
import json

def verify_c004_completeness():
    """Verify all stocks are present in C004 report."""
    print(f"\n{'='*80}")
    print(f"C004 AGGREGATION & COMPLETENESS VERIFICATION")
    print(f"{'='*80}\n")
    
    data_dir = project_root / "data" / "C004"
    if not data_dir.exists():
        print(f"❌ C004 directory not found: {data_dir}")
        return
    
    # Find all brokers/platforms
    print("📁 Checking folder structure...")
    brokers = []
    for item in data_dir.iterdir():
        if item.is_dir():
            brokers.append(item.name)
            file_count = len(list(item.glob("*.*")))
            print(f"   - {item.name}: {file_count} files")
    
    print(f"\n✓ Found {len(brokers)} brokers: {', '.join(brokers)}\n")
    
    # Process data
    print("🔄 Processing all files...")
    try:
        ingested_files = ingest_all_files(str(data_dir))
        print(f"✓ Ingested {len(ingested_files)} files")
        
        # Show ingestion breakdown
        broker_file_count = {}
        for file_info in ingested_files:
            broker = file_info['broker']
            broker_file_count[broker] = broker_file_count.get(broker, 0) + 1
        print(f"  Breakdown by broker:")
        for broker, count in broker_file_count.items():
            print(f"    - {broker}: {count} files")
        
        normalized_data = normalize_all_files(ingested_files)
        trades_df = normalized_data['trades']
        cg_df = normalized_data['capital_gains']
        print(f"✓ Normalized {len(trades_df)} trades, {len(cg_df)} capital gains\n")
    except Exception as e:
        print(f"❌ Error processing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if trades_df.empty:
        print("❌ No trade data found")
        return
    
    # Analyze trades data
    print("="*80)
    print("TRADES ANALYSIS")
    print("="*80)
    
    print(f"\n📊 Unique stocks traded: {trades_df['symbol'].nunique()}")
    print(f"📊 Total trade records: {len(trades_df)}")
    print(f"📊 Unique brokers: {trades_df['broker'].nunique()}")
    
    # Breakdown by broker
    print(f"\n🏢 Trades by Broker:")
    broker_stats = trades_df.groupby('broker').agg({
        'symbol': 'nunique',
        'qty': 'count'
    }).reset_index()
    broker_stats.columns = ['Broker', 'Unique Stocks', 'Trade Count']
    for _, row in broker_stats.iterrows():
        print(f"   - {row['Broker']}: {row['Unique Stocks']} stocks, {row['Trade Count']} trades")
    
    # All unique stocks
    all_stocks = sorted(trades_df['symbol'].unique())
    print(f"\n📈 All stocks traded ({len(all_stocks)}):")
    for i, stock in enumerate(all_stocks, 1):
        print(f"   {i:2d}. {stock}")
    
    # Compute holdings
    print(f"\n{'='*80}")
    print("HOLDINGS COMPUTATION")
    print("="*80)
    
    holdings_df = compute_current_holdings(trades_df, "C004")
    
    if holdings_df.empty:
        print(f"\n⚠️  WARNING: No current holdings computed!")
        print(f"   This means all positions are closed (fully sold)")
    else:
        print(f"\n✓ Current holdings: {len(holdings_df)} stocks")
        
        holdings_stocks = sorted(holdings_df['Asset Name'].unique())
        print(f"\n📊 Holdings stocks ({len(holdings_stocks)}):")
        for i, stock in enumerate(holdings_stocks, 1):
            holding = holdings_df[holdings_df['Asset Name'] == stock].iloc[0]
            print(f"   {i:2d}. {stock}: Qty={holding['Quantity']}, "
                  f"Platform={holding['Platform']}, "
                  f"Value=${holding['Current Value']:,.2f}")
    
    # Compare traded vs holdings
    print(f"\n{'='*80}")
    print("COMPLETENESS CHECK")
    print("="*80)
    
    traded_stocks = set(trades_df['symbol'].unique())
    holdings_stocks = set(holdings_df['Asset Name'].unique()) if not holdings_df.empty else set()
    closed_positions = traded_stocks - holdings_stocks
    
    print(f"\n📊 Stock Status:")
    print(f"   - Total traded: {len(traded_stocks)}")
    print(f"   - Current holdings: {len(holdings_stocks)}")
    print(f"   - Closed positions: {len(closed_positions)}")
    
    if closed_positions:
        print(f"\n🔒 Closed positions (fully sold, not in holdings):")
        for i, stock in enumerate(sorted(closed_positions), 1):
            # Get trade info
            stock_trades = trades_df[trades_df['symbol'] == stock]
            buy_qty = stock_trades[stock_trades['action'] == 'Buy']['qty'].sum()
            sell_qty = stock_trades[stock_trades['action'] == 'Sell']['qty'].sum()
            net_qty = buy_qty - sell_qty
            print(f"   {i:2d}. {stock}: Bought={buy_qty}, Sold={sell_qty}, Net={net_qty}")
    
    # Check for issues
    print(f"\n{'='*80}")
    print("ISSUE IDENTIFICATION")
    print("="*80)
    
    issues = []
    
    # Issue 1: Stocks traded on multiple brokers but only showing one
    print(f"\n🔍 Checking multi-broker stocks...")
    for stock in traded_stocks:
        stock_trades = trades_df[trades_df['symbol'] == stock]
        brokers_for_stock = stock_trades['broker'].unique()
        if len(brokers_for_stock) > 1:
            if stock in holdings_stocks:
                holding_broker = holdings_df[holdings_df['Asset Name'] == stock]['Platform'].iloc[0]
                print(f"   ⚠️  {stock}: Traded on {len(brokers_for_stock)} brokers "
                      f"({', '.join(brokers_for_stock)}), but holdings shows only: {holding_broker}")
                issues.append(f"{stock} multi-broker tracking issue")
    
    # Issue 2: Check for missing trades
    print(f"\n🔍 Checking data completeness...")
    expected_files = len(brokers) * 2  # Assuming at least tradebook + capital gains per broker
    if len(ingested_files) < expected_files:
        print(f"   ⚠️  Expected ~{expected_files} files, found {len(ingested_files)}")
        issues.append("Potentially missing files")
    
    # Issue 3: Check aggregation accuracy
    print(f"\n🔍 Checking aggregation accuracy...")
    if not holdings_df.empty:
        # Verify each holding
        for _, holding in holdings_df.iterrows():
            stock = holding['Asset Name']
            qty = holding['Quantity']
            
            # Calculate manually from trades
            stock_trades = trades_df[trades_df['symbol'] == stock]
            buy_qty = stock_trades[stock_trades['action'] == 'Buy']['qty'].sum()
            sell_qty = stock_trades[stock_trades['action'] == 'Sell']['qty'].sum()
            expected_qty = buy_qty - sell_qty
            
            if abs(float(qty) - float(expected_qty)) > 0.01:
                print(f"   ❌ {stock}: Holdings shows {qty}, expected {expected_qty}")
                issues.append(f"{stock} quantity mismatch")
    
    # Platform count verification
    print(f"\n🔍 Verifying platform count...")
    unique_brokers_in_trades = trades_df['broker'].nunique()
    unique_platforms_in_holdings = holdings_df['Platform'].nunique() if not holdings_df.empty else 0
    
    print(f"   - Brokers in trades: {unique_brokers_in_trades}")
    print(f"   - Platforms in holdings: {unique_platforms_in_holdings}")
    
    if unique_platforms_in_holdings < unique_brokers_in_trades:
        print(f"   ⚠️  Platform count issue detected")
        issues.append(f"Platform count mismatch ({unique_platforms_in_holdings} vs {unique_brokers_in_trades})")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    
    if not issues:
        print(f"\n✅ All checks passed! No issues detected.")
        print(f"   - All stocks properly aggregated")
        print(f"   - Holdings correctly computed")
        print(f"   - Platform count accurate")
    else:
        print(f"\n⚠️  Found {len(issues)} issues:\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"""
1. Multi-Broker Stock Tracking:
   - Current: Holdings show only the first broker per stock
   - Solution: Either split holdings by broker OR show all brokers
   
2. Closed Position Reporting:
   - Current: Closed positions don't appear in holdings (correct)
   - Note: They should appear in capital gains / transaction history
   
3. Platform Count Fix:
   - Status: Already fixed to count from trades data
   - Verify: Check report "Number of Platforms" field
   
4. Aggregation Method:
   - Current: Combines trades from all brokers per stock
   - Alternative: Keep separate rows per stock per broker
        """)
    
    # Generate report to verify
    print(f"\n{'='*80}")
    print("GENERATING REPORT")
    print("="*80)
    
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    try:
        from report_generator import generate_client_report
        generate_client_report(
            "C004",
            trades_df,
            cg_df,
            {},
            {},
            str(reports_dir)
        )
        report_path = reports_dir / "C004_portfolio_report.xlsx"
        print(f"\n✅ Report generated: {report_path}")
        print(f"   Open this file to verify:")
        print(f"   - Check 'Holdings' sheet for all current positions")
        print(f"   - Check 'Summary' sheet for platform count")
        print(f"   - Check 'Calculations' sheet for all trades")
    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_c004_completeness()
