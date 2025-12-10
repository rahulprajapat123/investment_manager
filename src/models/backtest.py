"""
Backtesting Engine for Investment Strategies
Tests trading strategies against historical data to evaluate performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database
from src.models.predict import StockPredictor

logger = logging.getLogger(__name__)


class Backtester:
    """
    Backtesting engine to evaluate trading strategies on historical data.
    Supports multiple strategies and provides comprehensive performance metrics.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital for backtesting (default $100,000)
        """
        self.initial_capital = initial_capital
        self.db = get_database()
        self.predictor = None
        self.trades = []
        self.portfolio_history = []
        
        # Try to load ML predictor
        try:
            self.predictor = StockPredictor()
            logger.info("ML predictor loaded for backtesting")
        except Exception as e:
            logger.warning(f"Could not load ML predictor: {e}")
    
    def run_ml_strategy(
        self, 
        tickers: List[str],
        start_date: str,
        end_date: str,
        confidence_threshold: float = 0.65,
        position_size_pct: float = 0.1
    ) -> Dict:
        """
        Backtest ML-based trading strategy.
        
        Strategy:
        - Buy when ML predicts UP with confidence > threshold
        - Sell when ML predicts DOWN with confidence > threshold
        - Position size = portfolio_value * position_size_pct
        
        Args:
            tickers: List of tickers to trade
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            confidence_threshold: Minimum confidence to execute trade (0-1)
            position_size_pct: Percentage of portfolio per position (0-1)
        
        Returns:
            Dictionary with backtest results and performance metrics
        """
        if not self.predictor:
            raise ValueError("ML predictor not available for backtesting")
        
        logger.info(f"Running ML strategy backtest from {start_date} to {end_date}")
        logger.info(f"Tickers: {tickers}, Confidence threshold: {confidence_threshold}")
        
        # Get historical data
        prices_df = self._load_historical_data(tickers, start_date, end_date)
        
        # Initialize portfolio
        cash = self.initial_capital
        positions = {ticker: 0 for ticker in tickers}  # shares held
        portfolio_values = []
        
        # Get unique dates
        dates = sorted(prices_df['date'].unique())
        
        for i, current_date in enumerate(dates[:-1]):  # Leave last day for exit
            # Get current prices
            current_prices = prices_df[prices_df['date'] == current_date].set_index('ticker')
            
            # Calculate current portfolio value
            portfolio_value = cash
            for ticker, shares in positions.items():
                if ticker in current_prices.index:
                    portfolio_value += shares * current_prices.loc[ticker, 'close']
            
            portfolio_values.append({
                'date': current_date,
                'value': portfolio_value,
                'cash': cash,
                'positions': positions.copy()
            })
            
            # Make predictions and execute trades
            for ticker in tickers:
                try:
                    # Get prediction
                    prediction = self.predictor.predict(ticker, current_date.strftime('%Y-%m-%d'))
                    
                    if not prediction:
                        continue
                    
                    direction = prediction['prediction']
                    confidence = prediction['probability_up'] if direction == 'UP' else prediction['probability_down']
                    
                    # Check if confidence meets threshold
                    if confidence < confidence_threshold:
                        continue
                    
                    # Get current price
                    if ticker not in current_prices.index:
                        continue
                    
                    current_price = current_prices.loc[ticker, 'close']
                    
                    # Execute trade based on prediction
                    if direction == 'UP' and positions[ticker] == 0:
                        # BUY signal - open position
                        position_value = portfolio_value * position_size_pct
                        shares_to_buy = int(position_value / current_price)
                        
                        if shares_to_buy > 0 and cash >= shares_to_buy * current_price:
                            cost = shares_to_buy * current_price
                            cash -= cost
                            positions[ticker] += shares_to_buy
                            
                            self.trades.append({
                                'date': current_date,
                                'ticker': ticker,
                                'action': 'BUY',
                                'shares': shares_to_buy,
                                'price': current_price,
                                'value': cost,
                                'confidence': confidence
                            })
                            
                    elif direction == 'DOWN' and positions[ticker] > 0:
                        # SELL signal - close position
                        shares_to_sell = positions[ticker]
                        proceeds = shares_to_sell * current_price
                        cash += proceeds
                        positions[ticker] = 0
                        
                        self.trades.append({
                            'date': current_date,
                            'ticker': ticker,
                            'action': 'SELL',
                            'shares': shares_to_sell,
                            'price': current_price,
                            'value': proceeds,
                            'confidence': confidence
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing {ticker} on {current_date}: {e}")
                    continue
        
        # Close all positions at end
        final_date = dates[-1]
        final_prices = prices_df[prices_df['date'] == final_date].set_index('ticker')
        
        for ticker, shares in positions.items():
            if shares > 0 and ticker in final_prices.index:
                final_price = final_prices.loc[ticker, 'close']
                proceeds = shares * final_price
                cash += proceeds
                
                self.trades.append({
                    'date': final_date,
                    'ticker': ticker,
                    'action': 'SELL',
                    'shares': shares,
                    'price': final_price,
                    'value': proceeds,
                    'confidence': 1.0
                })
        
        # Calculate final portfolio value
        final_value = cash
        
        portfolio_values.append({
            'date': final_date,
            'value': final_value,
            'cash': cash,
            'positions': {ticker: 0 for ticker in tickers}
        })
        
        # Calculate performance metrics
        metrics = self._calculate_metrics(portfolio_values, self.trades)
        
        return {
            'strategy': 'ML-Based',
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': ((final_value - self.initial_capital) / self.initial_capital) * 100,
            'metrics': metrics,
            'trades': self.trades,
            'portfolio_history': portfolio_values
        }
    
    def run_buy_hold_strategy(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        equal_weight: bool = True
    ) -> Dict:
        """
        Backtest simple buy-and-hold strategy.
        
        Strategy:
        - Buy equal amounts of all tickers on day 1
        - Hold until end date
        - Sell everything on last day
        
        Args:
            tickers: List of tickers to buy
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            equal_weight: If True, equal weight per ticker; else market cap weighted
        
        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Running buy-and-hold backtest from {start_date} to {end_date}")
        
        prices_df = self._load_historical_data(tickers, start_date, end_date)
        
        # Get first and last dates
        dates = sorted(prices_df['date'].unique())
        first_date = dates[0]
        last_date = dates[-1]
        
        # Get initial prices
        initial_prices = prices_df[prices_df['date'] == first_date].set_index('ticker')
        final_prices = prices_df[prices_df['date'] == last_date].set_index('ticker')
        
        # Allocate capital
        if equal_weight:
            capital_per_ticker = self.initial_capital / len(tickers)
        else:
            # For simplicity, use equal weight (market cap weighting requires additional data)
            capital_per_ticker = self.initial_capital / len(tickers)
        
        # Buy positions
        positions = {}
        total_invested = 0
        trades = []
        
        for ticker in tickers:
            if ticker in initial_prices.index:
                initial_price = initial_prices.loc[ticker, 'close']
                shares = int(capital_per_ticker / initial_price)
                cost = shares * initial_price
                
                positions[ticker] = shares
                total_invested += cost
                
                trades.append({
                    'date': first_date,
                    'ticker': ticker,
                    'action': 'BUY',
                    'shares': shares,
                    'price': initial_price,
                    'value': cost
                })
        
        # Calculate final value
        final_value = self.initial_capital - total_invested  # remaining cash
        
        for ticker, shares in positions.items():
            if ticker in final_prices.index:
                final_price = final_prices.loc[ticker, 'close']
                value = shares * final_price
                final_value += value
                
                trades.append({
                    'date': last_date,
                    'ticker': ticker,
                    'action': 'SELL',
                    'shares': shares,
                    'price': final_price,
                    'value': value
                })
        
        # Build portfolio history (simplified - just start and end)
        portfolio_history = [
            {'date': first_date, 'value': self.initial_capital},
            {'date': last_date, 'value': final_value}
        ]
        
        # Calculate daily portfolio values for metrics
        daily_values = []
        for date in dates:
            day_prices = prices_df[prices_df['date'] == date].set_index('ticker')
            day_value = self.initial_capital - total_invested
            
            for ticker, shares in positions.items():
                if ticker in day_prices.index:
                    day_value += shares * day_prices.loc[ticker, 'close']
            
            daily_values.append({
                'date': date,
                'value': day_value
            })
        
        metrics = self._calculate_metrics(daily_values, trades)
        
        return {
            'strategy': 'Buy-and-Hold',
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': ((final_value - self.initial_capital) / self.initial_capital) * 100,
            'metrics': metrics,
            'trades': trades,
            'portfolio_history': daily_values
        }
    
    def _load_historical_data(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Load historical price data for backtesting."""
        try:
            # Load from CSV
            prices_df = pd.read_csv('data/daily_prices.csv')
            prices_df['date'] = pd.to_datetime(prices_df['date'])
            
            # Filter by tickers and date range
            mask = (
                (prices_df['ticker'].isin(tickers)) &
                (prices_df['date'] >= start_date) &
                (prices_df['date'] <= end_date)
            )
            
            filtered_df = prices_df[mask].copy()
            
            if filtered_df.empty:
                raise ValueError(f"No data found for tickers {tickers} in date range")
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            raise
    
    def _calculate_metrics(
        self,
        portfolio_history: List[Dict],
        trades: List[Dict]
    ) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Metrics:
        - Total return (%)
        - Annualized return (%)
        - Sharpe ratio
        - Maximum drawdown (%)
        - Win rate (%)
        - Average win/loss
        - Number of trades
        """
        if not portfolio_history or len(portfolio_history) < 2:
            return {}
        
        # Convert to DataFrame
        df = pd.DataFrame(portfolio_history)
        df['returns'] = df['value'].pct_change()
        
        # Total return
        total_return = ((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0]) * 100
        
        # Annualized return (assuming daily data)
        days = len(df)
        years = days / 252  # Trading days per year
        annualized_return = ((df['value'].iloc[-1] / df['value'].iloc[0]) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Sharpe ratio (assuming risk-free rate = 2%)
        risk_free_rate = 0.02 / 252  # Daily risk-free rate
        excess_returns = df['returns'] - risk_free_rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252) if excess_returns.std() > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + df['returns']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Volatility (annualized)
        volatility = df['returns'].std() * np.sqrt(252) * 100
        
        # Trade statistics
        trade_metrics = self._calculate_trade_metrics(trades)
        
        return {
            'total_return_pct': round(total_return, 2),
            'annualized_return_pct': round(annualized_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'volatility_pct': round(volatility, 2),
            'total_trades': trade_metrics['total_trades'],
            'win_rate_pct': trade_metrics['win_rate'],
            'avg_win_pct': trade_metrics['avg_win'],
            'avg_loss_pct': trade_metrics['avg_loss'],
            'profit_factor': trade_metrics['profit_factor']
        }
    
    def _calculate_trade_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate trade-level performance metrics."""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        # Match buy/sell pairs
        positions = {}
        completed_trades = []
        
        for trade in trades:
            ticker = trade['ticker']
            
            if trade['action'] == 'BUY':
                if ticker not in positions:
                    positions[ticker] = []
                positions[ticker].append(trade)
                
            elif trade['action'] == 'SELL' and ticker in positions and positions[ticker]:
                # Match with most recent buy
                buy_trade = positions[ticker].pop()
                
                # Calculate P&L
                buy_value = buy_trade['shares'] * buy_trade['price']
                sell_value = trade['shares'] * trade['price']
                pnl = sell_value - buy_value
                pnl_pct = (pnl / buy_value) * 100
                
                completed_trades.append({
                    'ticker': ticker,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'is_win': pnl > 0
                })
        
        if not completed_trades:
            return {
                'total_trades': len(trades),
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
        
        # Calculate metrics
        total_trades = len(completed_trades)
        wins = [t for t in completed_trades if t['is_win']]
        losses = [t for t in completed_trades if not t['is_win']]
        
        win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        
        total_wins = sum([t['pnl'] for t in wins]) if wins else 0
        total_losses = abs(sum([t['pnl'] for t in losses])) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2)
        }
    
    def compare_strategies(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Compare ML strategy vs Buy-and-Hold.
        
        Returns:
            Comparison results with both strategies' performance
        """
        logger.info("Running strategy comparison...")
        
        # Run both strategies
        ml_results = self.run_ml_strategy(tickers, start_date, end_date)
        bh_results = self.run_buy_hold_strategy(tickers, start_date, end_date)
        
        # Calculate outperformance
        outperformance = ml_results['total_return'] - bh_results['total_return']
        
        return {
            'ml_strategy': ml_results,
            'buy_hold_strategy': bh_results,
            'outperformance_pct': round(outperformance, 2),
            'winner': 'ML Strategy' if outperformance > 0 else 'Buy-and-Hold'
        }


def run_backtest_example():
    """Example usage of backtesting engine."""
    
    # Initialize backtester
    backtester = Backtester(initial_capital=100000)
    
    # Define test parameters
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    start_date = '2024-01-01'
    end_date = '2024-12-31'
    
    print("\n" + "="*60)
    print("BACKTESTING ENGINE - STRATEGY COMPARISON")
    print("="*60)
    
    # Run comparison
    results = backtester.compare_strategies(tickers, start_date, end_date)
    
    # Print ML Strategy results
    print("\n📊 ML STRATEGY RESULTS:")
    print("-" * 60)
    ml = results['ml_strategy']
    print(f"Initial Capital:     ${ml['initial_capital']:,.2f}")
    print(f"Final Value:         ${ml['final_value']:,.2f}")
    print(f"Total Return:        {ml['total_return']:.2f}%")
    print(f"\nPerformance Metrics:")
    for key, value in ml['metrics'].items():
        print(f"  {key:25s}: {value}")
    print(f"Total Trades:        {len(ml['trades'])}")
    
    # Print Buy-and-Hold results
    print("\n📈 BUY-AND-HOLD RESULTS:")
    print("-" * 60)
    bh = results['buy_hold_strategy']
    print(f"Initial Capital:     ${bh['initial_capital']:,.2f}")
    print(f"Final Value:         ${bh['final_value']:,.2f}")
    print(f"Total Return:        {bh['total_return']:.2f}%")
    print(f"\nPerformance Metrics:")
    for key, value in bh['metrics'].items():
        print(f"  {key:25s}: {value}")
    
    # Print comparison
    print("\n🏆 COMPARISON:")
    print("-" * 60)
    print(f"Winner:              {results['winner']}")
    print(f"Outperformance:      {results['outperformance_pct']:.2f}%")
    print("\n" + "="*60)


if __name__ == '__main__':
    # Run example backtest
    run_backtest_example()
