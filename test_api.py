"""
Quick test script to verify API is working.
"""

import requests
import json

API_URL = "http://localhost:8080"

print("=" * 60)
print("TESTING INVESTMENT PLATFORM API")
print("=" * 60)
print()

# Test 1: Health Check
print("[1/5] Testing health endpoint...")
try:
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        print(f"  ✓ Health check passed")
        print(f"  Response: {response.json()}")
    else:
        print(f"  ✗ Health check failed: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 2: Get Portfolio
print("[2/5] Testing portfolio endpoint...")
try:
    response = requests.get(f"{API_URL}/api/portfolio/1")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Portfolio retrieved")
        print(f"  Client ID: {data['client_id']}")
        print(f"  Total Value: {data['total_value']}")
        print(f"  Gain/Loss: {data['total_gain_loss']}")
    else:
        print(f"  ✗ Failed: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 3: Get Stock Info
print("[3/5] Testing stock info endpoint...")
try:
    response = requests.get(f"{API_URL}/api/stock/AAPL")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Stock info retrieved")
        print(f"  Ticker: {data['ticker']}")
        print(f"  Current Price: ${data['price']['current']:.2f}")
        print(f"  Change: {data['change']['formatted']}")
    else:
        print(f"  ✗ Failed: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 4: Get Prediction
print("[4/5] Testing prediction endpoint...")
try:
    response = requests.get(f"{API_URL}/api/predict/AAPL")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Prediction retrieved")
        print(f"  Ticker: {data['ticker']}")
        print(f"  Direction: {data['prediction']['direction']}")
        print(f"  Probability UP: {data['prediction']['probability_up']}")
        print(f"  Recommendation: {data['recommendation']['action']} ({data['recommendation']['strength']})")
    else:
        print(f"  ✗ Failed: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 5: Get Recommendations
print("[5/5] Testing recommendations endpoint...")
try:
    response = requests.get(f"{API_URL}/api/recommendations?action=BUY&limit=3")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Recommendations retrieved")
        print(f"  Action: {data['action']}")
        print(f"  Count: {data['count']}")
        if data['count'] > 0:
            print(f"  Top recommendation: {data['recommendations'][0]['ticker']} (Confidence: {data['recommendations'][0]['confidence']})")
    else:
        print(f"  ✗ Failed: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

print("=" * 60)
print("API TESTING COMPLETE!")
print("=" * 60)
