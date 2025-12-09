"""
Database utilities for local CSV and BigQuery operations.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List
import logging
from config import Config

logger = logging.getLogger(__name__)

class LocalDatabase:
    """
    Local CSV-based database for demo.
    In production, this would be replaced with BigQuery.
    """
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Config.DATA_DIR
        self.cache = {}
    
    def load_daily_prices(self, ticker: Optional[str] = None) -> pd.DataFrame:
        """Load daily price data."""
        if 'daily_prices' not in self.cache:
            file_path = self.data_dir / 'daily_prices.csv'
            self.cache['daily_prices'] = pd.read_csv(file_path)
            self.cache['daily_prices']['date'] = pd.to_datetime(self.cache['daily_prices']['date'])
        
        df = self.cache['daily_prices'].copy()
        
        if ticker:
            df = df[df['ticker'] == ticker]
        
        return df.sort_values('date')
    
    def load_portfolio_holdings(self, client_id: Optional[int] = None) -> pd.DataFrame:
        """Load portfolio holdings."""
        file_path = self.data_dir / 'portfolio_holdings.csv'
        df = pd.read_csv(file_path)
        df['purchase_date'] = pd.to_datetime(df['purchase_date'])
        
        if client_id:
            df = df[df['client_id'] == client_id]
        
        return df
    
    def load_news_sentiment(self, ticker: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """Load news sentiment data."""
        file_path = self.data_dir / 'news_sentiment.csv'
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter recent days
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
        df = df[df['date'] >= cutoff_date]
        
        if ticker:
            df = df[df['ticker'] == ticker]
        
        return df.sort_values('date', ascending=False)
    
    def load_market_data(self, index_name: str = 'SP500') -> pd.DataFrame:
        """Load market index data."""
        file_path = self.data_dir / 'market_data.csv'
        df = pd.read_csv(file_path)
        df['date'] = pd.to_datetime(df['date'])
        
        if index_name:
            df = df[df['index_name'] == index_name]
        
        return df.sort_values('date')
    
    def load_client_profiles(self, client_id: Optional[int] = None) -> pd.DataFrame:
        """Load client profile data."""
        file_path = self.data_dir / 'client_profiles.csv'
        df = pd.read_csv(file_path)
        
        if client_id:
            df = df[df['client_id'] == client_id]
        
        return df
    
    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get the most recent closing price for a ticker."""
        df = self.load_daily_prices(ticker=ticker)
        if df.empty:
            return None
        return df.iloc[-1]['close']
    
    def get_historical_returns(self, ticker: str, days: int = 30) -> pd.Series:
        """Get historical daily returns."""
        df = self.load_daily_prices(ticker=ticker)
        df = df.tail(days + 1)  # Need one extra day for returns
        returns = df['close'].pct_change().dropna()
        return returns
    
    def get_portfolio_value(self, client_id: int) -> dict:
        """Calculate total portfolio value for a client."""
        holdings = self.load_portfolio_holdings(client_id=client_id)
        
        total_value = 0
        total_cost = 0
        positions = []
        
        for _, row in holdings.iterrows():
            current_price = self.get_latest_price(row['ticker'])
            if current_price is None:
                continue
            
            position_value = row['shares'] * current_price
            position_cost = row['shares'] * row['cost_basis']
            gain_loss = position_value - position_cost
            gain_loss_pct = (gain_loss / position_cost) * 100 if position_cost > 0 else 0
            
            total_value += position_value
            total_cost += position_cost
            
            positions.append({
                'ticker': row['ticker'],
                'shares': row['shares'],
                'cost_basis': row['cost_basis'],
                'current_price': current_price,
                'position_value': position_value,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct
            })
        
        return {
            'client_id': client_id,
            'total_value': total_value,
            'total_cost': total_cost,
            'total_gain_loss': total_value - total_cost,
            'total_gain_loss_pct': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
            'positions': positions
        }
    
    def get_portfolio_data(self, client_id: int):
        """
        Get portfolio data for report generation (returns raw numeric values).
        
        Args:
            client_id: Client ID
            
        Returns:
            dict: Portfolio data with positions
        """
        portfolio = self.get_portfolio(client_id)
        
        if not portfolio:
            return None
        
        # Convert formatted strings back to numbers for calculations
        total_value_str = portfolio['total_value'].replace('$', '').replace(',', '')
        total_cost_str = portfolio['total_cost'].replace('$', '').replace(',', '')
        
        total_value = float(total_value_str)
        total_cost = float(total_cost_str)
        
        return {
            'client_id': client_id,
            'total_value': portfolio['total_value'],  # Keep formatted
            'total_cost': portfolio['total_cost'],
            'total_gain_loss': portfolio['total_gain_loss'],
            'total_gain_loss_pct': portfolio['total_gain_loss_pct'],
            'total_value_raw': total_value,  # Raw numbers
            'total_cost_raw': total_cost,
            'positions': portfolio['positions']
        }


class BigQueryDatabase:
    """
    BigQuery database wrapper for production use.
    """
    
    def __init__(self, project_id: str = None):
        try:
            from google.cloud import bigquery
            self.project_id = project_id or Config.GCP_PROJECT_ID
            self.client = bigquery.Client(project=self.project_id)
            self.dataset_id = Config.DATASET_ID
            logger.info(f"Connected to BigQuery project: {self.project_id}")
        except Exception as e:
            logger.warning(f"BigQuery not available: {e}")
            self.client = None
    
    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame."""
        if not self.client:
            raise RuntimeError("BigQuery client not initialized")
        
        query_job = self.client.query(sql)
        return query_job.to_dataframe()
    
    def load_table(self, table_name: str, dataframe: pd.DataFrame):
        """Load a DataFrame into a BigQuery table."""
        if not self.client:
            raise RuntimeError("BigQuery client not initialized")
        
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        job = self.client.load_table_from_dataframe(dataframe, table_id)
        job.result()  # Wait for completion
        logger.info(f"Loaded {len(dataframe)} rows into {table_id}")


# Factory function to get appropriate database
def get_database():
    """Get database instance based on configuration."""
    if Config.USE_LOCAL_DATA:
        return LocalDatabase()
    else:
        return BigQueryDatabase()
