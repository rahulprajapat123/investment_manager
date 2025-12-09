"""
Machine Learning utilities for feature engineering and model operations.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

class FeatureEngineer:
    """
    Feature engineering for stock prediction.
    """
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame, periods: List[int] = [1, 5, 10, 30]) -> pd.DataFrame:
        """Calculate returns over multiple periods."""
        df = df.copy()
        
        for period in periods:
            df[f'return_{period}d'] = df['close'].pct_change(periods=period)
        
        return df
    
    @staticmethod
    def calculate_volatility(df: pd.DataFrame, windows: List[int] = [10, 30, 60]) -> pd.DataFrame:
        """Calculate rolling volatility."""
        df = df.copy()
        
        # First calculate daily returns if not already present
        if 'return_1d' not in df.columns:
            df['return_1d'] = df['close'].pct_change()
        
        for window in windows:
            df[f'volatility_{window}d'] = df['return_1d'].rolling(window).std()
        
        return df
    
    @staticmethod
    def calculate_moving_averages(df: pd.DataFrame, windows: List[int] = [50, 200]) -> pd.DataFrame:
        """Calculate simple moving averages."""
        df = df.copy()
        
        for window in windows:
            df[f'sma_{window}'] = df['close'].rolling(window).mean()
        
        # Golden cross signal
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            df['golden_cross'] = (df['sma_50'] > df['sma_200']).astype(int)
        
        return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Relative Strength Index."""
        df = df.copy()
        
        # Calculate price changes
        delta = df['close'].diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Calculate MACD indicator."""
        df = df.copy()
        
        # Calculate EMAs
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        # MACD line
        df['macd'] = ema_fast - ema_slow
        
        # Signal line
        df['macd_signal'] = df['macd'].ewm(span=signal, adjust=False).mean()
        
        # MACD histogram
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    @staticmethod
    def add_sentiment_features(price_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
        """Add sentiment features to price data."""
        df = price_df.copy()
        
        # Aggregate sentiment by date and ticker
        sentiment_agg = sentiment_df.groupby(['date', 'ticker']).agg({
            'sentiment_score': ['mean', 'std', 'count']
        }).reset_index()
        
        sentiment_agg.columns = ['date', 'ticker', 'sentiment_mean', 'sentiment_std', 'news_count']
        
        # Merge with price data
        df = df.merge(sentiment_agg, on=['date', 'ticker'], how='left')
        
        # Fill missing sentiment with neutral
        df['sentiment_mean'] = df['sentiment_mean'].fillna(0)
        df['sentiment_std'] = df['sentiment_std'].fillna(0)
        df['news_count'] = df['news_count'].fillna(0)
        
        return df
    
    @staticmethod
    def create_target(df: pd.DataFrame, forward_days: int = 1, threshold: float = 0.0) -> pd.DataFrame:
        """
        Create target variable for classification.
        Target = 1 if stock goes up in next N days, else 0.
        """
        df = df.copy()
        
        # Calculate forward return
        df['forward_return'] = df['close'].pct_change(periods=forward_days).shift(-forward_days)
        
        # Binary target: 1 if up, 0 if down
        df['target'] = (df['forward_return'] > threshold).astype(int)
        
        return df
    
    @staticmethod
    def engineer_all_features(price_df: pd.DataFrame, sentiment_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Apply all feature engineering steps.
        """
        logger.info("Engineering features...")
        
        df = price_df.copy()
        
        # Technical indicators
        df = FeatureEngineer.calculate_returns(df)
        df = FeatureEngineer.calculate_volatility(df)
        df = FeatureEngineer.calculate_moving_averages(df)
        df = FeatureEngineer.calculate_rsi(df)
        df = FeatureEngineer.calculate_macd(df)
        
        # Add sentiment if available
        if sentiment_df is not None and not sentiment_df.empty:
            df = FeatureEngineer.add_sentiment_features(df, sentiment_df)
        
        # Create target
        df = FeatureEngineer.create_target(df)
        
        logger.info(f"Created {len(df.columns)} features")
        
        return df
    
    @staticmethod
    def get_feature_columns() -> List[str]:
        """Get list of feature columns for modeling."""
        return [
            'return_1d', 'return_5d', 'return_10d', 'return_30d',
            'volatility_10d', 'volatility_30d', 'volatility_60d',
            'sma_50', 'sma_200', 'golden_cross',
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'sentiment_mean', 'sentiment_std', 'news_count',
            'volume'
        ]


class ModelEvaluator:
    """
    Utilities for model evaluation.
    """
    
    @staticmethod
    def calculate_metrics(y_true, y_pred, y_pred_proba=None) -> dict:
        """Calculate classification metrics."""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0)
        }
        
        if y_pred_proba is not None:
            metrics['auc'] = roc_auc_score(y_true, y_pred_proba)
        
        return metrics
    
    @staticmethod
    def print_metrics(metrics: dict):
        """Pretty print metrics."""
        print("\n" + "="*50)
        print("MODEL EVALUATION METRICS")
        print("="*50)
        for key, value in metrics.items():
            print(f"{key.upper():.<20} {value:.4f}")
        print("="*50 + "\n")
    
    @staticmethod
    def plot_confusion_matrix(y_true, y_pred):
        """Plot confusion matrix."""
        from sklearn.metrics import confusion_matrix
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.tight_layout()
        
        return plt
    
    @staticmethod
    def plot_feature_importance(model, feature_names: List[str], top_n: int = 15):
        """Plot feature importance."""
        import matplotlib.pyplot as plt
        
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
            
            # Create DataFrame
            feat_imp = pd.DataFrame({
                'feature': feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False).head(top_n)
            
            # Plot
            plt.figure(figsize=(10, 6))
            plt.barh(feat_imp['feature'], feat_imp['importance'])
            plt.xlabel('Importance')
            plt.title(f'Top {top_n} Feature Importances')
            plt.gca().invert_yaxis()
            plt.tight_layout()
            
            return plt
        else:
            logger.warning("Model does not have feature_importances_ attribute")
            return None
