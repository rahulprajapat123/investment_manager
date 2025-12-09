"""
Unit tests for the investment platform.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.helpers import (
    validate_ticker,
    format_currency,
    format_percentage,
    calculate_sharpe_ratio,
    generate_recommendation
)
from src.utils.ml_utils import FeatureEngineer


class TestHelpers:
    """Test helper functions."""
    
    def test_validate_ticker(self):
        """Test ticker validation."""
        assert validate_ticker('AAPL') == True
        assert validate_ticker('MSFT') == True
        assert validate_ticker('aapl') == False  # Lowercase
        assert validate_ticker('TOOLONG') == False  # Too long
        assert validate_ticker('123') == False  # Numbers
        assert validate_ticker('') == False  # Empty
        assert validate_ticker(None) == False  # None
    
    def test_format_currency(self):
        """Test currency formatting."""
        assert format_currency(1000) == '$1,000.00'
        assert format_currency(1234.56) == '$1,234.56'
        assert format_currency(0) == '$0.00'
    
    def test_format_percentage(self):
        """Test percentage formatting."""
        assert format_percentage(5.5) == '+5.50%'
        assert format_percentage(-3.2) == '-3.20%'
        assert format_percentage(0) == '+0.00%'
    
    def test_generate_recommendation(self):
        """Test recommendation generation."""
        # Strong buy
        rec = generate_recommendation(0.85)
        assert rec['action'] == 'BUY'
        assert rec['strength'] == 'Strong'
        
        # Moderate buy
        rec = generate_recommendation(0.70)
        assert rec['action'] == 'BUY'
        assert rec['strength'] == 'Moderate'
        
        # Hold
        rec = generate_recommendation(0.55)
        assert rec['action'] == 'HOLD'
        
        # Strong sell
        rec = generate_recommendation(0.15)
        assert rec['action'] == 'SELL'


class TestFeatureEngineer:
    """Test feature engineering."""
    
    @pytest.fixture
    def sample_prices(self):
        """Create sample price data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        data = {
            'date': dates,
            'ticker': 'AAPL',
            'open': 150 + pd.Series(range(100)) * 0.5,
            'high': 152 + pd.Series(range(100)) * 0.5,
            'low': 148 + pd.Series(range(100)) * 0.5,
            'close': 150 + pd.Series(range(100)) * 0.5,
            'volume': 50000000
        }
        return pd.DataFrame(data)
    
    def test_calculate_returns(self, sample_prices):
        """Test return calculation."""
        df = FeatureEngineer.calculate_returns(sample_prices, periods=[1, 5])
        
        assert 'return_1d' in df.columns
        assert 'return_5d' in df.columns
        assert not df['return_1d'].isna().all()
    
    def test_calculate_volatility(self, sample_prices):
        """Test volatility calculation."""
        df = FeatureEngineer.calculate_volatility(sample_prices, windows=[10])
        
        assert 'volatility_10d' in df.columns
    
    def test_calculate_moving_averages(self, sample_prices):
        """Test moving average calculation."""
        df = FeatureEngineer.calculate_moving_averages(sample_prices, windows=[10, 20])
        
        assert 'sma_10' in df.columns
        assert 'sma_20' in df.columns
    
    def test_calculate_rsi(self, sample_prices):
        """Test RSI calculation."""
        df = FeatureEngineer.calculate_rsi(sample_prices)
        
        assert 'rsi' in df.columns
        # RSI should be between 0 and 100
        assert df['rsi'].dropna().between(0, 100).all()
    
    def test_create_target(self, sample_prices):
        """Test target creation."""
        df = FeatureEngineer.create_target(sample_prices)
        
        assert 'target' in df.columns
        assert 'forward_return' in df.columns
        # Target should be binary (0 or 1)
        assert df['target'].dropna().isin([0, 1]).all()


class TestDatabase:
    """Test database operations."""
    
    def test_load_daily_prices(self):
        """Test loading price data."""
        from src.utils.database import LocalDatabase
        from config import Config
        
        Config.validate()
        db = LocalDatabase()
        
        # This will only work if data has been generated
        try:
            df = db.load_daily_prices()
            assert not df.empty
            assert 'ticker' in df.columns
            assert 'close' in df.columns
        except FileNotFoundError:
            pytest.skip("Data files not generated yet")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
