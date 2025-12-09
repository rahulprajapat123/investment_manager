"""
Test script for the Investment Platform Web Interface.
Validates all functionality including API endpoints and UI components.
"""

import requests
import time
import sys

API_BASE_URL = 'http://localhost:8080'

def print_test_header(test_name):
    """Print formatted test header."""
    print("\n" + "="*70)
    print(f"TEST: {test_name}")
    print("="*70)

def test_api_health():
    """Test API health endpoint."""
    print_test_header("API Health Check")
    try:
        response = requests.get(f'{API_BASE_URL}/health', timeout=5)
        data = response.json()
        
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Database: {data.get('database')}")
        print(f"✓ ML Enabled: {data.get('ml_enabled')}")
        print(f"✓ Status: {data.get('status')}")
        
        assert response.status_code == 200, "Health check failed"
        assert data.get('status') == 'healthy', "API not healthy"
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_portfolio_endpoint():
    """Test portfolio endpoint."""
    print_test_header("Portfolio Endpoint")
    try:
        client_ids = [1, 2, 3, 4, 5]
        
        for client_id in client_ids:
            response = requests.get(f'{API_BASE_URL}/api/portfolio/{client_id}', timeout=5)
            data = response.json()
            
            print(f"\n  Client {client_id}:")
            print(f"  - Total Value: ${data['total_value']:,.2f}")
            print(f"  - Total Cost: ${data['total_cost']:,.2f}")
            print(f"  - Gain/Loss: ${data['total_gain_loss']:,.2f} ({data['total_gain_loss_pct']:.2f}%)")
            print(f"  - Holdings: {len(data['holdings'])} positions")
            
            assert response.status_code == 200, f"Portfolio request failed for client {client_id}"
            assert 'total_value' in data, "Missing total_value"
            assert 'holdings' in data, "Missing holdings"
        
        print(f"\n✓ All {len(client_ids)} client portfolios loaded successfully")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_stock_info_endpoint():
    """Test stock info endpoint."""
    print_test_header("Stock Info Endpoint")
    try:
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
        
        for ticker in tickers:
            response = requests.get(f'{API_BASE_URL}/api/stock/{ticker}', timeout=5)
            data = response.json()
            
            print(f"\n  {ticker}:")
            print(f"  - Price: ${data['current_price']:.2f}")
            print(f"  - Change: {data['price_change']:.2f}%")
            print(f"  - Volume: {data.get('volume', 'N/A')}")
            
            assert response.status_code == 200, f"Stock info request failed for {ticker}"
            assert 'current_price' in data, "Missing current_price"
        
        print(f"\n✓ All {len(tickers)} stock info requests successful")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_prediction_endpoint():
    """Test prediction endpoint."""
    print_test_header("Stock Prediction Endpoint")
    try:
        tickers = ['AAPL', 'TSLA', 'NVDA']
        
        for ticker in tickers:
            response = requests.get(f'{API_BASE_URL}/api/predict/{ticker}', timeout=5)
            data = response.json()
            
            pred = data['prediction']
            rec = pred['recommendation']
            
            print(f"\n  {ticker}:")
            print(f"  - Direction: {pred['predicted_direction']}")
            print(f"  - Probability UP: {pred['probability_up']*100:.2f}%")
            print(f"  - Probability DOWN: {pred['probability_down']*100:.2f}%")
            print(f"  - Recommendation: {rec['action']} ({rec['strength']})")
            print(f"  - Confidence: {rec['confidence']*100:.2f}%")
            
            assert response.status_code == 200, f"Prediction request failed for {ticker}"
            assert 'prediction' in data, "Missing prediction"
            assert 'predicted_direction' in pred, "Missing predicted_direction"
        
        print(f"\n✓ All {len(tickers)} prediction requests successful")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_recommendations_endpoint():
    """Test recommendations endpoint."""
    print_test_header("Recommendations Endpoint")
    try:
        actions = ['BUY', 'SELL', 'HOLD']
        
        for action in actions:
            response = requests.get(f'{API_BASE_URL}/api/recommendations?action={action}', timeout=5)
            data = response.json()
            
            print(f"\n  {action} Recommendations:")
            print(f"  - Count: {data['count']}")
            
            if data['recommendations']:
                for i, rec in enumerate(data['recommendations'][:3], 1):
                    print(f"  - [{i}] {rec['ticker']}: {rec['action']} ({rec['strength']}, {rec['confidence']*100:.1f}% confidence)")
            
            assert response.status_code == 200, f"Recommendations request failed for {action}"
            assert 'recommendations' in data, "Missing recommendations"
        
        print(f"\n✓ All recommendation requests successful")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_top_stocks_endpoint():
    """Test top stocks endpoint."""
    print_test_header("Top Stocks Endpoint")
    try:
        response = requests.get(f'{API_BASE_URL}/api/top-stocks?limit=10', timeout=5)
        data = response.json()
        
        print(f"\n  Top 10 Stocks by Performance:")
        for i, stock in enumerate(data['top_stocks'][:10], 1):
            print(f"  [{i}] {stock['ticker']}: ${stock['price']:.2f} ({stock['change']:+.2f}%)")
        
        assert response.status_code == 200, "Top stocks request failed"
        assert 'top_stocks' in data, "Missing top_stocks"
        assert len(data['top_stocks']) > 0, "No stocks returned"
        
        print(f"\n✓ Top stocks endpoint successful")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_web_interface():
    """Test that the web interface is accessible."""
    print_test_header("Web Interface Accessibility")
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Content Type: {response.headers.get('Content-Type')}")
        print(f"✓ Content Length: {len(response.content)} bytes")
        
        # Check if HTML is returned
        assert response.status_code == 200, "Web interface not accessible"
        assert 'html' in response.headers.get('Content-Type', ''), "Not serving HTML"
        assert b'Investment Platform' in response.content, "Missing expected content"
        
        print(f"✓ Web interface is accessible at {API_BASE_URL}")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def test_static_files():
    """Test that static files are accessible."""
    print_test_header("Static Files Accessibility")
    try:
        files = [
            '/static/css/style.css',
            '/static/js/app.js'
        ]
        
        for file_path in files:
            response = requests.get(f'{API_BASE_URL}{file_path}', timeout=5)
            print(f"  {file_path}: {response.status_code} ({len(response.content)} bytes)")
            assert response.status_code == 200, f"Static file not accessible: {file_path}"
        
        print(f"\n✓ All static files accessible")
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False

def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  INVESTMENT PLATFORM WEB INTERFACE TEST SUITE".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    tests = [
        ("API Health Check", test_api_health),
        ("Web Interface", test_web_interface),
        ("Static Files", test_static_files),
        ("Portfolio Endpoint", test_portfolio_endpoint),
        ("Stock Info Endpoint", test_stock_info_endpoint),
        ("Prediction Endpoint", test_prediction_endpoint),
        ("Recommendations Endpoint", test_recommendations_endpoint),
        ("Top Stocks Endpoint", test_top_stocks_endpoint),
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed")
    print(f"Time: {elapsed_time:.2f} seconds")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Web interface is ready for demonstration.")
        print(f"\n📊 Access the dashboard at: {API_BASE_URL}")
        print("\nFeatures available:")
        print("  • Portfolio tracking for 5 clients")
        print("  • Real-time stock information")
        print("  • ML-powered stock predictions")
        print("  • Buy/Sell/Hold recommendations")
        print("  • Market overview with top performers")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
