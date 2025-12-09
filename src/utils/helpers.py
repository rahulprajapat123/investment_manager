"""
Helper utilities for the investment platform.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

# Configure logging
def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

logger = logging.getLogger(__name__)


def validate_ticker(ticker: str) -> bool:
    """Validate stock ticker format."""
    if not ticker or not isinstance(ticker, str):
        return False
    
    # Basic validation: 1-5 uppercase letters
    return ticker.isupper() and 1 <= len(ticker) <= 5 and ticker.isalpha()


def format_currency(value: float) -> str:
    """Format number as currency."""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format number as percentage."""
    return f"{value:+.2f}%"


def calculate_portfolio_metrics(positions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate portfolio-level metrics.
    
    Args:
        positions: List of position dictionaries
        
    Returns:
        Dictionary with portfolio metrics
    """
    if not positions:
        return {
            'total_value': 0,
            'total_gain_loss': 0,
            'total_gain_loss_pct': 0,
            'num_positions': 0,
            'winners': 0,
            'losers': 0
        }
    
    total_value = sum(p['position_value'] for p in positions)
    total_cost = sum(p['shares'] * p['cost_basis'] for p in positions)
    total_gain_loss = total_value - total_cost
    total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
    
    winners = sum(1 for p in positions if p['gain_loss'] > 0)
    losers = sum(1 for p in positions if p['gain_loss'] < 0)
    
    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_gain_loss': total_gain_loss,
        'total_gain_loss_pct': total_gain_loss_pct,
        'num_positions': len(positions),
        'winners': winners,
        'losers': losers,
        'win_rate': (winners / len(positions) * 100) if positions else 0
    }


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe Ratio.
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate (default 2%)
        
    Returns:
        Sharpe ratio
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    
    # Annualize returns and volatility (assuming daily returns)
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * (252 ** 0.5)
    
    sharpe = (annual_return - risk_free_rate) / annual_volatility
    
    return sharpe


def calculate_max_drawdown(prices: pd.Series) -> float:
    """
    Calculate maximum drawdown.
    
    Args:
        prices: Series of prices
        
    Returns:
        Maximum drawdown as percentage
    """
    if prices.empty:
        return 0.0
    
    # Calculate cumulative returns
    cumulative = (1 + prices.pct_change()).cumprod()
    
    # Calculate running maximum
    running_max = cumulative.expanding().max()
    
    # Calculate drawdown
    drawdown = (cumulative - running_max) / running_max
    
    # Return maximum drawdown as percentage
    return drawdown.min() * 100


def get_business_days(start_date: datetime, end_date: datetime) -> int:
    """Calculate number of business days between two dates."""
    return len(pd.bdate_range(start_date, end_date))


def is_market_open(dt: datetime = None) -> bool:
    """
    Check if market is currently open.
    Simplified version - assumes NYSE hours.
    """
    if dt is None:
        dt = datetime.now()
    
    # Check if weekday (0 = Monday, 4 = Friday)
    if dt.weekday() > 4:
        return False
    
    # Check time (9:30 AM - 4:00 PM EST)
    market_open = dt.replace(hour=9, minute=30, second=0)
    market_close = dt.replace(hour=16, minute=0, second=0)
    
    return market_open <= dt <= market_close


def get_risk_category(volatility: float) -> str:
    """
    Categorize risk based on volatility.
    
    Args:
        volatility: Annualized volatility
        
    Returns:
        Risk category string
    """
    if volatility < 0.15:
        return 'Low'
    elif volatility < 0.25:
        return 'Moderate'
    elif volatility < 0.35:
        return 'High'
    else:
        return 'Very High'


def generate_recommendation(prediction_proba: float, confidence_threshold: float = 0.65) -> Dict[str, Any]:
    """
    Generate trading recommendation based on prediction probability.
    
    Args:
        prediction_proba: Probability of upward movement (0-1)
        confidence_threshold: Minimum confidence for strong recommendation
        
    Returns:
        Recommendation dictionary
    """
    if prediction_proba >= confidence_threshold:
        action = 'BUY'
        strength = 'Strong' if prediction_proba >= 0.75 else 'Moderate'
    elif prediction_proba <= (1 - confidence_threshold):
        action = 'SELL'
        strength = 'Strong' if prediction_proba <= 0.25 else 'Moderate'
    else:
        action = 'HOLD'
        strength = 'Neutral'
    
    return {
        'action': action,
        'strength': strength,
        'confidence': prediction_proba if action == 'BUY' else (1 - prediction_proba),
        'probability_up': prediction_proba,
        'probability_down': 1 - prediction_proba
    }


def chunked(items: list, chunk_size: int):
    """
    Yield successive chunks from list.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Yields:
        Chunks of the list
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


class PerformanceTimer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"Starting: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"Completed: {self.name} ({elapsed:.2f}s)")
