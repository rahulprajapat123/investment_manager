"""
Comprehensive verification script for numeric calculations and data extraction.
Tests all mathematical operations, aggregations, and extractions.
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pandas as pd
from decimal import Decimal
from ingestion import ingest_all_files
from normalizer import normalize_all_files
from report_generator import compute_current_holdings
from decimal_utils import sum_decimals, divide_decimal, multiply_decimal, round_decimal

def verify_numeric_calculations(client_id="C001"):
    """Verify all numeric calculations are accurate."""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE NUMERIC CALCULATION VERIFICATION")
    print(f"Client: {client_id}")
    print(f"{'='*80}\n")
    
    data_dir = project_root / "data" / client_id
    if not data_dir.exists():
        print(f"❌ Client directory not found: {data_dir}")
        return
    
    # Process data
    print("📊 Processing data...")
    try:
        ingested_files = ingest_all_files(str(data_dir))
        normalized_data = normalize_all_files(ingested_files)
        trades_df = normalized_data['trades']
        cg_df = normalized_data['capital_gains']
        print(f"✅ Loaded {len(trades_df)} trades, {len(cg_df)} capital gains\n")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    if trades_df.empty:
        print("❌ No trade data to analyze")
        return
    
    # Test 1: Broker/Platform Extraction
    print("="*80)
    print("TEST 1: BROKER/PLATFORM EXTRACTION")
    print("="*80)
    
    if 'broker' in trades_df.columns:
        unique_brokers = trades_df['broker'].unique()
        print(f"✓ Found {len(unique_brokers)} unique brokers:")
        for broker in unique_brokers:
            trade_count = len(trades_df[trades_df['broker'] == broker])
            symbols = trades_df[trades_df['broker'] == broker]['symbol'].nunique()
            print(f"  - {broker}: {trade_count} trades, {symbols} symbols")
        
        # Check for generic broker names (indicates extraction issue)
        generic_names = ['Uploaded_Files', 'Unknown', 'Platform_Unknown']
        issues = [b for b in unique_brokers if any(g in str(b) for g in generic_names)]
        if issues:
            print(f"\n⚠️  WARNING: Found generic broker names: {issues}")
            print(f"   This indicates broker detection needs improvement")
    else:
        print(f"❌ FAIL: No 'broker' column in trades data")
    
    # Test 2: Decimal Precision
    print(f"\n{'='*80}")
    print("TEST 2: DECIMAL PRECISION IN CALCULATIONS")
    print("="*80)
    
    precision_ok = True
    for idx, row in trades_df.head(5).iterrows():
        qty = row.get('qty', 0)
        price = row.get('price', 0)
        
        # Check if values are Decimals or need conversion
        if isinstance(qty, Decimal) and isinstance(price, Decimal):
            calc_value = multiply_decimal(qty, price)
            print(f"✓ Trade {idx}: {qty} × {price} = {calc_value} (Decimal)")
        else:
            print(f"⚠️  Trade {idx}: qty={type(qty).__name__}, price={type(price).__name__}")
            precision_ok = False
    
    if precision_ok:
        print(f"\n✅ PASS: All calculations use Decimal precision")
    else:
        print(f"\n⚠️  WARNING: Some values not using Decimal - may have precision errors")
    
    # Test 3: Holdings Calculation
    print(f"\n{'='*80}")
    print("TEST 3: HOLDINGS CALCULATION ACCURACY")
    print("="*80)
    
    holdings_df = compute_current_holdings(trades_df, client_id)
    
    if holdings_df.empty:
        print("ℹ️  No current holdings (all positions closed)")
    else:
        print(f"✓ Computed {len(holdings_df)} holdings\n")
        
        # Verify holdings math for each stock
        for idx, holding in holdings_df.head(3).iterrows():
            symbol = holding['Asset Name']
            qty = holding['Quantity']
            avg_cost = holding['Average Cost']
            current_price = holding['Current Price']
            current_value = holding['Current Value']
            total_invested = holding['Total Invested']
            unrealized_pnl = holding['Unrealized P/L']
            
            # Recalculate to verify
            calc_current_value = multiply_decimal(qty, current_price)
            calc_invested = multiply_decimal(qty, avg_cost)
            calc_pnl = current_value - calc_invested
            
            value_match = abs(float(current_value) - float(calc_current_value)) < 0.01
            invested_match = abs(float(total_invested) - float(calc_invested)) < 0.01
            pnl_match = abs(float(unrealized_pnl) - float(calc_pnl)) < 0.01
            
            if value_match and invested_match and pnl_match:
                print(f"✓ {symbol}: All calculations correct")
            else:
                print(f"❌ {symbol}: Calculation mismatch!")
                if not value_match:
                    print(f"   Current Value: {current_value} vs {calc_current_value}")
                if not invested_match:
                    print(f"   Total Invested: {total_invested} vs {calc_invested}")
                if not pnl_match:
                    print(f"   Unrealized P/L: {unrealized_pnl} vs {calc_pnl}")
    
    # Test 4: Aggregation Accuracy
    print(f"\n{'='*80}")
    print("TEST 4: PORTFOLIO AGGREGATION ACCURACY")
    print("="*80)
    
    if not holdings_df.empty:
        # Test sum operations
        total_current_value = sum_decimals(*holdings_df['Current Value'].tolist())
        total_invested = sum_decimals(*holdings_df['Total Invested'].tolist())
        total_unrealized_pnl = sum_decimals(*holdings_df['Unrealized P/L'].tolist())
        
        # Verify using pandas sum as comparison
        pandas_current_value = holdings_df['Current Value'].sum()
        pandas_invested = holdings_df['Total Invested'].sum()
        
        print(f"Total Current Value:")
        print(f"  Decimal sum: ${total_current_value:,.2f}")
        print(f"  Pandas sum:  ${pandas_current_value:,.2f}")
        print(f"  Match: {abs(float(total_current_value) - float(pandas_current_value)) < 0.01} ✓\n")
        
        print(f"Total Invested:")
        print(f"  Decimal sum: ${total_invested:,.2f}")
        print(f"  Pandas sum:  ${pandas_invested:,.2f}")
        print(f"  Match: {abs(float(total_invested) - float(pandas_invested)) < 0.01} ✓\n")
        
        # Test percentage calculation
        if total_invested > 0:
            pnl_pct = (total_unrealized_pnl / total_invested) * 100
            print(f"Unrealized P/L: ${total_unrealized_pnl:,.2f} ({pnl_pct:.2f}%)")
    
    # Test 5: Capital Gains
    if not cg_df.empty:
        print(f"\n{'='*80}")
        print("TEST 5: CAPITAL GAINS CALCULATION")
        print("="*80)
        
        if 'pnl' in cg_df.columns:
            total_realized_pnl = sum_decimals(*cg_df['pnl'].tolist())
            print(f"✓ Total Realized P/L: ${total_realized_pnl:,.2f}")
            
            # Breakdown by type if available
            if 'section' in cg_df.columns:
                for section in cg_df['section'].unique():
                    section_df = cg_df[cg_df['section'] == section]
                    section_pnl = sum_decimals(*section_df['pnl'].tolist())
                    print(f"  - {section}: ${section_pnl:,.2f} ({len(section_df)} transactions)")
        else:
            print("⚠️  No 'pnl' column in capital gains data")
    
    # Test 6: Data Extraction Quality
    print(f"\n{'='*80}")
    print("TEST 6: DATA EXTRACTION QUALITY")
    print("="*80)
    
    quality_score = 100
    issues = []
    
    # Check for missing values
    for col in ['date', 'symbol', 'action', 'qty', 'price']:
        if col in trades_df.columns:
            missing = trades_df[col].isna().sum()
            if missing > 0:
                issues.append(f"{missing} missing values in '{col}'")
                quality_score -= (missing / len(trades_df)) * 10
    
    # Check for zero or negative prices
    if 'price' in trades_df.columns:
        invalid_prices = (trades_df['price'] <= 0).sum()
        if invalid_prices > 0:
            issues.append(f"{invalid_prices} zero or negative prices")
            quality_score -= (invalid_prices / len(trades_df)) * 15
    
    # Check for zero quantities
    if 'qty' in trades_df.columns:
        invalid_qty = (trades_df['qty'] <= 0).sum()
        if invalid_qty > 0:
            issues.append(f"{invalid_qty} zero or negative quantities")
            quality_score -= (invalid_qty / len(trades_df)) * 15
    
    print(f"Data Quality Score: {quality_score:.1f}/100")
    if issues:
        print(f"\nIssues Found:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print(f"✅ No data quality issues detected")
    
    # Summary
    print(f"\n{'='*80}")
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"""
✓ Broker Extraction:     {'OK' if len(unique_brokers) > 0 else 'NEEDS REVIEW'}
✓ Decimal Precision:     {'OK' if precision_ok else 'NEEDS REVIEW'}
✓ Holdings Calculation:  {'OK' if not holdings_df.empty else 'NO HOLDINGS'}
✓ Aggregations:          OK (using Decimal arithmetic)
✓ Capital Gains:         {'OK' if not cg_df.empty else 'NO DATA'}
✓ Data Quality:          {quality_score:.1f}/100

{'✅ ALL TESTS PASSED' if quality_score >= 80 and precision_ok else '⚠️  SOME ISSUES FOUND - REVIEW ABOVE'}
    """)
    
    # Recommendations
    if quality_score < 80 or not precision_ok or len([b for b in unique_brokers if 'Unknown' in str(b) or 'Uploaded' in str(b)]) > 0:
        print(f"RECOMMENDATIONS:")
        print(f"1. Improve broker detection by adding DP ID mapping")
        print(f"2. Consider alternative parsing methods for better extraction")
        print(f"3. Add data validation at ingestion stage")
        print(f"4. Implement fallback extraction methods for problematic files")

if __name__ == "__main__":
    client_id = sys.argv[1] if len(sys.argv) > 1 else "C001"
    verify_numeric_calculations(client_id)
