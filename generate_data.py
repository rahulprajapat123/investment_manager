"""
Generate synthetic datasets for the investment platform demo.
This creates realistic market data, portfolio holdings, and news sentiment.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define stock universe
TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'WMT',
           'JNJ', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'DIS', 'NFLX', 'ADBE', 'CRM']

def generate_daily_prices(start_date='2020-01-01', end_date='2024-12-06', tickers=TICKERS):
    """
    Generate daily price data for stocks.
    Includes: date, ticker, open, high, low, close, volume
    """
    print("Generating daily prices dataset...")
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    date_range = pd.date_range(start, end, freq='B')  # Business days only
    
    data = []
    
    for ticker in tickers:
        # Random initial price between $50 and $500
        base_price = random.uniform(50, 500)
        price = base_price
        
        for date in date_range:
            # Simulate daily price movement
            daily_return = np.random.normal(0.0005, 0.02)  # Mean return 0.05%, std 2%
            price = price * (1 + daily_return)
            
            # Generate OHLC
            open_price = price * (1 + np.random.normal(0, 0.005))
            close_price = price
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            # Volume between 1M and 50M
            volume = int(np.random.uniform(1_000_000, 50_000_000))
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'ticker': ticker,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
    
    df = pd.DataFrame(data)
    df.to_csv('data/daily_prices.csv', index=False)
    print(f"✓ Created daily_prices.csv with {len(df):,} rows")
    return df

def generate_portfolio_holdings(tickers=TICKERS[:10]):
    """
    Generate portfolio holdings for demo users.
    Includes: client_id, client_name, email, ticker, shares, cost_basis, purchase_date
    """
    print("Generating portfolio holdings dataset...")
    
    clients = [
        {'client_id': 1, 'name': 'John Smith', 'email': 'john.smith@email.com'},
        {'client_id': 2, 'name': 'Jane Doe', 'email': 'jane.doe@email.com'},
        {'client_id': 3, 'name': 'Robert Johnson', 'email': 'robert.j@email.com'},
        {'client_id': 4, 'name': 'Emily Davis', 'email': 'emily.davis@email.com'},
        {'client_id': 5, 'name': 'Michael Brown', 'email': 'michael.b@email.com'},
    ]
    
    data = []
    
    for client in clients:
        # Each client holds 3-8 different stocks
        num_holdings = random.randint(3, 8)
        client_tickers = random.sample(tickers, num_holdings)
        
        for ticker in client_tickers:
            shares = random.randint(10, 500)
            cost_basis = round(random.uniform(50, 400), 2)
            purchase_date = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
            
            data.append({
                'client_id': client['client_id'],
                'client_name': client['name'],
                'client_email': client['email'],
                'ticker': ticker,
                'shares': shares,
                'cost_basis': cost_basis,
                'purchase_date': purchase_date
            })
    
    df = pd.DataFrame(data)
    df.to_csv('data/portfolio_holdings.csv', index=False)
    print(f"✓ Created portfolio_holdings.csv with {len(df):,} rows")
    return df

def generate_news_sentiment(tickers=TICKERS, days=90):
    """
    Generate news sentiment data.
    Includes: date, ticker, headline, sentiment_score, source
    """
    print("Generating news sentiment dataset...")
    
    headlines_templates = [
        "{ticker} reports strong quarterly earnings",
        "{ticker} announces new product launch",
        "{ticker} stock drops on market concerns",
        "{ticker} beats analyst expectations",
        "{ticker} faces regulatory challenges",
        "{ticker} CEO announces strategic partnership",
        "{ticker} releases innovative technology",
        "{ticker} stock rallies on positive outlook",
        "Analysts upgrade {ticker} rating",
        "{ticker} expands into new markets",
    ]
    
    sources = ['Reuters', 'Bloomberg', 'CNBC', 'Wall Street Journal', 'Financial Times']
    
    data = []
    end_date = datetime.now()
    
    for i in range(days):
        date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # 2-5 news items per day
        for _ in range(random.randint(2, 5)):
            ticker = random.choice(tickers)
            headline = random.choice(headlines_templates).format(ticker=ticker)
            
            # Sentiment score between -1 (negative) and 1 (positive)
            # Bias slightly positive
            sentiment_score = round(np.random.normal(0.1, 0.4), 3)
            sentiment_score = max(-1, min(1, sentiment_score))  # Clamp to [-1, 1]
            
            source = random.choice(sources)
            
            data.append({
                'date': date,
                'ticker': ticker,
                'headline': headline,
                'sentiment_score': sentiment_score,
                'source': source
            })
    
    df = pd.DataFrame(data)
    df.to_csv('data/news_sentiment.csv', index=False)
    print(f"✓ Created news_sentiment.csv with {len(df):,} rows")
    return df

def generate_market_data(days=1260):
    """
    Generate market indices data (S&P 500, etc.)
    Includes: date, index_name, value, daily_return
    """
    print("Generating market data dataset...")
    
    end_date = datetime.now()
    date_range = pd.date_range(end_date - timedelta(days=days), end_date, freq='B')
    
    # Simulate S&P 500
    sp500_base = 3000
    sp500_values = [sp500_base]
    
    for _ in range(len(date_range) - 1):
        daily_return = np.random.normal(0.0004, 0.012)  # Market return
        sp500_values.append(sp500_values[-1] * (1 + daily_return))
    
    data = []
    for i, date in enumerate(date_range):
        value = sp500_values[i]
        daily_return = 0 if i == 0 else (sp500_values[i] - sp500_values[i-1]) / sp500_values[i-1]
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'index_name': 'SP500',
            'value': round(value, 2),
            'daily_return': round(daily_return, 6)
        })
    
    df = pd.DataFrame(data)
    df.to_csv('data/market_data.csv', index=False)
    print(f"✓ Created market_data.csv with {len(df):,} rows")
    return df

def generate_client_profiles():
    """
    Generate client profile data.
    Includes: client_id, risk_tolerance, investment_goal, time_horizon
    """
    print("Generating client profiles dataset...")
    
    data = [
        {
            'client_id': 1,
            'risk_tolerance': 'moderate',
            'investment_goal': 'growth',
            'time_horizon_years': 10,
            'age': 35
        },
        {
            'client_id': 2,
            'risk_tolerance': 'aggressive',
            'investment_goal': 'growth',
            'time_horizon_years': 15,
            'age': 28
        },
        {
            'client_id': 3,
            'risk_tolerance': 'conservative',
            'investment_goal': 'income',
            'time_horizon_years': 5,
            'age': 55
        },
        {
            'client_id': 4,
            'risk_tolerance': 'moderate',
            'investment_goal': 'balanced',
            'time_horizon_years': 8,
            'age': 42
        },
        {
            'client_id': 5,
            'risk_tolerance': 'aggressive',
            'investment_goal': 'growth',
            'time_horizon_years': 20,
            'age': 25
        },
    ]
    
    df = pd.DataFrame(data)
    df.to_csv('data/client_profiles.csv', index=False)
    print(f"✓ Created client_profiles.csv with {len(df):,} rows")
    return df

if __name__ == '__main__':
    print("=" * 60)
    print("INVESTMENT PLATFORM - DATA GENERATION")
    print("=" * 60)
    print()
    
    # Generate all datasets
    daily_prices_df = generate_daily_prices()
    portfolio_df = generate_portfolio_holdings()
    sentiment_df = generate_news_sentiment()
    market_df = generate_market_data()
    profiles_df = generate_client_profiles()
    
    print()
    print("=" * 60)
    print("DATA GENERATION COMPLETE!")
    print("=" * 60)
    print()
    print("Generated files in 'data/' folder:")
    print("  - daily_prices.csv")
    print("  - portfolio_holdings.csv")
    print("  - news_sentiment.csv")
    print("  - market_data.csv")
    print("  - client_profiles.csv")
    print()
    print("Total records:", 
          f"{len(daily_prices_df) + len(portfolio_df) + len(sentiment_df) + len(market_df) + len(profiles_df):,}")
