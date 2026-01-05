"""
Debug script to test calculation accuracy including platforms count and other numeric data.
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
import json

def test_client_calculations(client_id="C001"):
    """Test calculations for a specific client."""
    print(f"\n{'='*70}")
    print(f"Testing Calculations for Client: {client_id}")
    print(f"{'='*70}\n")
    
    # Check if client data exists
    data_dir = project_root / "data" / client_id
    if not data_dir.exists():
        print(f"❌ ERROR: Client directory does not exist: {data_dir}")
        return
    
    print(f"📁 Client directory: {data_dir}")
    
    # Find all uploaded files
    uploaded_files_dir = data_dir / "Uploaded_Files"
    if uploaded_files_dir.exists():
        files = list(uploaded_files_dir.glob("*"))
        print(f"\n📄 Found {len(files)} files:")
        for f in files:
            print(f"   - {f.name}")
    else:
        print(f"⚠️  No Uploaded_Files directory found")
        return
    
    # Run ingestion and normalization directly
    print(f"\n🔄 Processing data...")
    try:
        # Ingest
        ingested_files = ingest_all_files(str(data_dir))
        print(f"✅ Ingested {len(ingested_files)} files")
        
        # Normalize
        normalized_data = normalize_all_files(ingested_files)
        trades_df = normalized_data['trades']
        cg_df = normalized_data['capital_gains']
        print(f"✅ Normalized {len(trades_df)} trade records")
        print(f"✅ Normalized {len(cg_df)} capital gains records")
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if trades_df.empty:
        print(f"\n❌ No trade data to analyze")
        return
    
    # Analyze platform/broker information
    print(f"\n{'='*70}")
    print(f"PLATFORM/BROKER ANALYSIS")
    print(f"{'='*70}")
    
    print(f"\n📌 Unique brokers in trades data:")
    if 'broker' in trades_df.columns:
        brokers = trades_df['broker'].unique()
        print(f"   Count: {len(brokers)}")
        for broker in sorted(brokers):
            count = len(trades_df[trades_df['broker'] == broker])
            print(f"   - {broker}: {count} trades")
    else:
        print(f"   ❌ 'broker' column not found in trades!")
    
    # Compute holdings
    print(f"\n🏠 Computing current holdings...")
    holdings_df = compute_current_holdings(trades_df, client_id)
    
    if holdings_df.empty:
        print(f"   ⚠️  No current holdings (all positions closed)")
    else:
        print(f"   ✅ {len(holdings_df)} active holdings")
        
        # Platform count from holdings
        if 'Platform' in holdings_df.columns:
            platforms = holdings_df['Platform'].unique()
            platform_count = len(platforms)
            print(f"\n📊 Platforms in holdings:")
            print(f"   Count: {platform_count}")
            for platform in sorted(platforms):
                count = len(holdings_df[holdings_df['Platform'] == platform])
                total_value = holdings_df[holdings_df['Platform'] == platform]['Current Value'].sum()
                print(f"   - {platform}: {count} holdings, Value: {total_value}")
        else:
            print(f"   ❌ 'Platform' column not found in holdings!")
    
    # Numeric calculations verification
    print(f"\n{'='*70}")
    print(f"NUMERIC CALCULATIONS VERIFICATION")
    print(f"{'='*70}")
    
    if not holdings_df.empty:
        from decimal import Decimal
        from decimal_utils import sum_decimals
        
        total_current_value = sum_decimals(*holdings_df['Current Value'].tolist())
        total_invested = sum_decimals(*holdings_df['Total Invested'].tolist())
        unrealized_pnl = sum_decimals(*holdings_df['Unrealized P/L'].tolist())
        
        print(f"\n💰 Portfolio Metrics:")
        print(f"   Total Current Value: ${total_current_value:,.2f}")
        print(f"   Total Invested: ${total_invested:,.2f}")
        print(f"   Unrealized P/L: ${unrealized_pnl:,.2f}")
        
        if total_invested > 0:
            pnl_pct = (unrealized_pnl / total_invested) * 100
            print(f"   Unrealized P/L %: {pnl_pct:.2f}%")
    
    if not cg_df.empty:
        from decimal_utils import sum_decimals
        realized_pnl = sum_decimals(*cg_df['pnl'].tolist()) if 'pnl' in cg_df.columns else Decimal("0")
        print(f"   Realized P/L: ${realized_pnl:,.2f}")
    
    # Check for potential issues
    print(f"\n{'='*70}")
    print(f"POTENTIAL ISSUES")
    print(f"{'='*70}")
    
    issues = []
    
    # Issue 1: Platform count doesn't match broker count
    if 'broker' in trades_df.columns and 'Platform' in holdings_df.columns:
        unique_brokers_in_trades = len(trades_df['broker'].unique())
        unique_platforms_in_holdings = holdings_df['Platform'].nunique()
        
        if unique_platforms_in_holdings != unique_brokers_in_trades:
            issues.append(
                f"Platform count mismatch: {unique_platforms_in_holdings} platforms in holdings "
                f"vs {unique_brokers_in_trades} brokers in trades. "
                f"This occurs when a stock is bought from multiple brokers but only the "
                f"first broker is recorded in holdings."
            )
    
    # Issue 2: Holdings only show first broker per symbol
    if not holdings_df.empty and not trades_df.empty:
        for symbol in holdings_df['Asset Name'].unique():
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            if 'broker' in symbol_trades.columns:
                brokers_for_symbol = symbol_trades['broker'].unique()
                if len(brokers_for_symbol) > 1:
                    holding_platform = holdings_df[holdings_df['Asset Name'] == symbol]['Platform'].iloc[0]
                    issues.append(
                        f"Stock '{symbol}' traded on {len(brokers_for_symbol)} brokers "
                        f"({', '.join(brokers_for_symbol)}), but holdings only shows: {holding_platform}"
                    )
    
    # Issue 3: Check for closed positions not in holdings
    if not trades_df.empty:
        all_traded_symbols = trades_df['symbol'].unique()
        holdings_symbols = holdings_df['Asset Name'].unique() if not holdings_df.empty else []
        closed_positions = set(all_traded_symbols) - set(holdings_symbols)
        if closed_positions:
            issues.append(
                f"{len(closed_positions)} stocks have been fully sold (closed positions): "
                f"{', '.join(list(closed_positions)[:5])}{'...' if len(closed_positions) > 5 else ''}"
            )
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"\n⚠️  Issue {i}:")
            print(f"   {issue}")
    else:
        print(f"\n✅ No issues detected")
    
    # Recommendations
    print(f"\n{'='*70}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*70}")
    
    print(f"""
1. Platform Count Issue:
   Current logic: Counts unique platforms from holdings (where each holding 
   gets the broker from its FIRST trade only).
   
   Better approach: Count unique brokers from ALL trades data.
   
2. Holdings Platform Assignment:
   Current: Each stock gets platform from first chronological trade.
   
   Better approaches:
   a) Split holdings by broker (one row per stock per broker)
   b) Use most recent/largest position broker
   c) List all brokers for each stock
   
3. Numeric Calculations:
   Currently using Decimal for precision - ✅ Good
   All calculations appear to use proper aggregation functions - ✅ Good
   
4. Alternative Extraction Methods:
   If current parsing fails, consider:
   - Direct CSV parsing (if data is CSV)
   - Custom regex patterns for each broker format
   - Manual column mapping interface
   - OCR for scanned documents
    """)


if __name__ == "__main__":
    import sys
    client_id = sys.argv[1] if len(sys.argv) > 1 else "C001"
    test_client_calculations(client_id)
