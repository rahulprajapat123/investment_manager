"""
Make predictions using trained model.
"""

import pandas as pd
import numpy as np
import joblib
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database
from src.utils.ml_utils import FeatureEngineer
from src.utils.helpers import setup_logging, generate_recommendation

logger = logging.getLogger(__name__)


class StockPredictor:
    """
    Stock direction prediction using trained ML model.
    """
    
    def __init__(self, model_name: str = None, model_version: str = None):
        """
        Initialize predictor with trained model.
        
        Args:
            model_name: Name of the model (default from config)
            model_version: Version of the model (default from config)
        """
        self.model_name = model_name or Config.MODEL_NAME
        self.model_version = model_version or Config.MODEL_VERSION
        
        # Load model
        model_path = Config.get_model_file(f'{self.model_name}_{self.model_version}.pkl')
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")
        
        # Load feature columns
        features_path = Config.get_model_file(f'{self.model_name}_{self.model_version}_features.pkl')
        self.feature_cols = joblib.load(features_path)
        logger.info(f"Loaded {len(self.feature_cols)} feature columns")
        
        # Load metadata
        metadata_path = Config.get_model_file(f'{self.model_name}_{self.model_version}_metadata.pkl')
        if metadata_path.exists():
            self.metadata = joblib.load(metadata_path)
            logger.info(f"Model accuracy: {self.metadata['metrics']['accuracy']:.2%}")
        else:
            self.metadata = {}
    
    def prepare_features(self, ticker: str, as_of_date: str = None) -> pd.DataFrame:
        """
        Prepare features for a single ticker.
        
        Args:
            ticker: Stock ticker
            as_of_date: Date to prepare features for (default: latest)
            
        Returns:
            DataFrame with features
        """
        db = get_database()
        
        # Load price data
        prices_df = db.load_daily_prices(ticker=ticker)
        
        if prices_df.empty:
            raise ValueError(f"No price data found for {ticker}")
        
        # Load sentiment data
        sentiment_df = db.load_news_sentiment(ticker=ticker, days=90)
        
        # Engineer features
        features_df = FeatureEngineer.engineer_all_features(prices_df, sentiment_df)
        
        # Filter to specific date if provided
        if as_of_date:
            as_of_date = pd.to_datetime(as_of_date)
            features_df = features_df[features_df['date'] <= as_of_date]
        
        return features_df
    
    def predict(self, ticker: str, as_of_date: str = None) -> dict:
        """
        Predict stock direction for a ticker.
        
        Args:
            ticker: Stock ticker
            as_of_date: Date to make prediction for (default: latest)
            
        Returns:
            Dictionary with prediction results
        """
        # Prepare features
        features_df = self.prepare_features(ticker, as_of_date)
        
        if features_df.empty:
            raise ValueError(f"No features available for {ticker}")
        
        # Get latest row
        latest = features_df.iloc[-1]
        
        # Extract feature values
        X = pd.DataFrame([latest[self.feature_cols]])
        
        # Handle missing features
        X = X.fillna(0)
        
        # Make prediction
        prediction = self.model.predict(X)[0]
        prediction_proba = self.model.predict_proba(X)[0]
        
        # Generate recommendation
        recommendation = generate_recommendation(prediction_proba[1])
        
        return {
            'ticker': ticker,
            'date': latest['date'],
            'current_price': latest['close'],
            'prediction': 'UP' if prediction == 1 else 'DOWN',
            'probability_up': prediction_proba[1],
            'probability_down': prediction_proba[0],
            'recommendation': recommendation,
            'features': {
                'return_30d': latest.get('return_30d', None),
                'volatility_30d': latest.get('volatility_30d', None),
                'rsi': latest.get('rsi', None),
                'sentiment_mean': latest.get('sentiment_mean', None)
            }
        }
    
    def predict_multiple(self, tickers: list, as_of_date: str = None) -> list:
        """
        Predict for multiple tickers.
        
        Args:
            tickers: List of stock tickers
            as_of_date: Date to make predictions for
            
        Returns:
            List of prediction dictionaries
        """
        results = []
        
        for ticker in tickers:
            try:
                prediction = self.predict(ticker, as_of_date)
                results.append(prediction)
            except Exception as e:
                logger.warning(f"Prediction failed for {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'error': str(e)
                })
        
        return results
    
    def get_top_recommendations(self, tickers: list, top_n: int = 5, action: str = 'BUY') -> list:
        """
        Get top stock recommendations.
        
        Args:
            tickers: List of tickers to analyze
            top_n: Number of top recommendations
            action: Filter by action (BUY/SELL/HOLD)
            
        Returns:
            List of top recommendations
        """
        # Get predictions for all tickers
        predictions = self.predict_multiple(tickers)
        
        # Filter out errors
        valid_predictions = [p for p in predictions if 'error' not in p]
        
        # Filter by action
        if action:
            valid_predictions = [
                p for p in valid_predictions 
                if p['recommendation']['action'] == action
            ]
        
        # Sort by confidence
        sorted_predictions = sorted(
            valid_predictions,
            key=lambda x: x['recommendation']['confidence'],
            reverse=True
        )
        
        return sorted_predictions[:top_n]


def main():
    """Demo prediction."""
    setup_logging()
    
    # Initialize predictor
    predictor = StockPredictor()
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
    print("\n" + "="*60)
    print("STOCK DIRECTION PREDICTIONS")
    print("="*60 + "\n")
    
    for ticker in test_tickers:
        try:
            result = predictor.predict(ticker)
            
            print(f"\n{ticker}:")
            print(f"  Current Price: ${result['current_price']:.2f}")
            print(f"  Prediction: {result['prediction']}")
            print(f"  Probability UP: {result['probability_up']:.1%}")
            print(f"  Recommendation: {result['recommendation']['action']} ({result['recommendation']['strength']})")
            print(f"  Confidence: {result['recommendation']['confidence']:.1%}")
            
        except Exception as e:
            print(f"\n{ticker}: Error - {e}")
    
    # Get top BUY recommendations
    print("\n" + "="*60)
    print("TOP 5 BUY RECOMMENDATIONS")
    print("="*60 + "\n")
    
    top_buys = predictor.get_top_recommendations(test_tickers, top_n=5, action='BUY')
    
    for i, rec in enumerate(top_buys, 1):
        print(f"{i}. {rec['ticker']} - Confidence: {rec['recommendation']['confidence']:.1%}")


if __name__ == '__main__':
    main()
