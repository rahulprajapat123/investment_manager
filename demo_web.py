"""
Quick Web Interface Demo Script
Tests the web interface manually with browser automation prompts
"""

import webbrowser
import time

API_URL = 'http://localhost:8080'

print("\n" + "="*70)
print(" 🎯 INVESTMENT PLATFORM WEB INTERFACE DEMONSTRATION")
print("="*70)

print("\n✓ Web interface is running at:", API_URL)
print("\n📋 TESTING CHECKLIST:")
print("\n1. Portfolio Tab:")
print("   - View Client 1 portfolio (default)")
print("   - Switch between clients using dropdown")
print("   - See total value, cost, gain/loss, and positions")
print("   - View holdings table with 4 stocks")

print("\n2. Stock Predictions Tab:")
print("   - Enter 'AAPL' and click Predict")
print("   - See prediction direction (UP/DOWN)")
print("   - View probabilities and recommendation")
print("   - Check key features (30D return, RSI, volatility, sentiment)")
print("   - Try other tickers: TSLA, NVDA, META, GOOGL")

print("\n3. Recommendations Tab:")
print("   - Click 'Buy' button (may be empty)")
print("   - Click 'Sell' button (may be empty)")
print("   - Click 'Hold' button (should show 5 recommendations)")
print("   - View ticker, direction, confidence, and strength")

print("\n4. Market Overview Tab:")
print("   - View top 10 performing stocks")
print("   - See ticker, current price, and daily change %")
print("   - Ranked from best to worst performance")

print("\n" + "="*70)
print(" 🚀 OPENING WEB INTERFACE IN BROWSER...")
print("="*70)

# Open in default browser
webbrowser.open(API_URL)

print("\n✓ Browser opened!")
print("\n📊 The dashboard should display:")
print("   • 4 navigation tabs at the top")
print("   • Connected status indicator (green)")
print("   • Portfolio data for Client 1")
print("   • Modern, responsive design")

print("\n" + "="*70)
print(" ✅ DEMONSTRATION COMPLETE")
print("="*70)
print("\n💡 Tips:")
print("   • API runs on port 8080")
print("   • All data is synthetic for demo purposes")
print("   • ML model accuracy is ~52% (demo only)")
print("   • Refresh every 30 seconds automatically")

print("\n📖 For deployment to GCP, see: docs/GCP_DEPLOYMENT_GUIDE.md")
print("\n" + "="*70 + "\n")
