"""
Test script to verify multi-platform processing
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ingestion import ingest_all_files
from normalizer import normalize_all_files
import pandas as pd

def test_multiplatform_processing(client_id="C003"):
    """Test that files from multiple platforms are processed correctly"""
    
    print(f"\n{'='*80}")
    print(f"Testing Multi-Platform Processing for {client_id}")
    print(f"{'='*80}\n")
    
    data_dir = Path("data") / client_id
    
    if not data_dir.exists():
        print(f"❌ Client directory not found: {data_dir}")
        return
    
    # Check folder structure
    print("📁 Checking folder structure...")
    broker_folders = [d for d in data_dir.iterdir() if d.is_dir()]
    print(f"   Found {len(broker_folders)} broker folders:")
    
    for broker_folder in broker_folders:
        files = list(broker_folder.glob("*.xlsx")) + list(broker_folder.glob("*.xls")) + list(broker_folder.glob("*.csv"))
        print(f"   - {broker_folder.name}: {len(files)} files")
        for f in files:
            print(f"     • {f.name}")
    
    # Test ingestion
    print(f"\n📥 Testing ingestion...")
    try:
        ingested_files = ingest_all_files(str(data_dir.parent))
        
        # Filter for this client
        client_files = [f for f in ingested_files if client_id in str(f['file_path'])]
        
        print(f"   ✅ Ingested {len(client_files)} files for {client_id}")
        
        # Group by broker
        brokers = {}
        for f in client_files:
            broker = f['broker']
            if broker not in brokers:
                brokers[broker] = []
            brokers[broker].append(f['file_type'])
        
        print(f"\n   Brokers detected: {len(brokers)}")
        for broker, file_types in brokers.items():
            print(f"   - {broker}: {', '.join(file_types)}")
        
    except Exception as e:
        print(f"   ❌ Ingestion failed: {e}")
        return
    
    # Test normalization
    print(f"\n🔄 Testing normalization...")
    try:
        normalized = normalize_all_files(ingested_files)
        
        trades_df = normalized['trades']
        cg_df = normalized['capital_gains']
        
        # Filter for this client
        client_trades = trades_df[trades_df['client_id'] == client_id]
        client_cg = cg_df[cg_df['client_id'] == client_id]
        
        print(f"   ✅ Normalized {len(client_trades)} trade records")
        print(f"   ✅ Normalized {len(client_cg)} capital gains records")
        
        # Count unique platforms
        unique_brokers = client_trades['broker'].nunique() if len(client_trades) > 0 else 0
        
        print(f"\n📊 Platform Analysis:")
        print(f"   Total platforms with data: {unique_brokers}")
        
        if len(client_trades) > 0:
            broker_summary = client_trades.groupby('broker').agg({
                'symbol': 'count',
                'quantity': 'sum',
                'total_value': 'sum'
            }).rename(columns={'symbol': 'trade_count'})
            
            print(f"\n   Platform Details:")
            for broker, row in broker_summary.iterrows():
                print(f"   - {broker}:")
                print(f"     • Trades: {int(row['trade_count'])}")
                print(f"     • Total Quantity: {int(row['quantity'])}")
                print(f"     • Total Value: ₹{row['total_value']:,.2f}")
        
    except Exception as e:
        print(f"   ❌ Normalization failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n{'='*80}")
    print(f"✅ Multi-Platform Processing Test Completed")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    # Test with C003 by default, or pass client_id as argument
    client_id = sys.argv[1] if len(sys.argv) > 1 else "C003"
    test_multiplatform_processing(client_id)
