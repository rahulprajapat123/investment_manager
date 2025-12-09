"""
Train machine learning model for stock direction prediction.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database
from src.utils.ml_utils import FeatureEngineer, ModelEvaluator
from src.utils.helpers import setup_logging, PerformanceTimer

logger = logging.getLogger(__name__)


def prepare_training_data():
    """
    Prepare data for model training.
    """
    with PerformanceTimer("Data preparation"):
        # Load data
        db = get_database()
        prices_df = db.load_daily_prices()
        sentiment_df = db.load_news_sentiment(days=1825)  # 5 years
        
        logger.info(f"Loaded {len(prices_df):,} price records")
        logger.info(f"Loaded {len(sentiment_df):,} sentiment records")
        
        # Engineer features for each ticker
        all_features = []
        
        for ticker in prices_df['ticker'].unique():
            ticker_prices = prices_df[prices_df['ticker'] == ticker].copy()
            ticker_sentiment = sentiment_df[sentiment_df['ticker'] == ticker].copy()
            
            # Engineer features
            ticker_features = FeatureEngineer.engineer_all_features(
                ticker_prices,
                ticker_sentiment
            )
            
            ticker_features['ticker'] = ticker
            all_features.append(ticker_features)
        
        # Combine all tickers
        features_df = pd.concat(all_features, ignore_index=True)
        
        logger.info(f"Created feature dataset with {len(features_df):,} rows")
        
        return features_df


def train_model(features_df: pd.DataFrame):
    """
    Train Random Forest model.
    """
    with PerformanceTimer("Model training"):
        # Get feature columns
        feature_cols = FeatureEngineer.get_feature_columns()
        
        # Filter to only available features
        feature_cols = [col for col in feature_cols if col in features_df.columns]
        
        # Remove rows with missing target or features
        df = features_df.dropna(subset=['target'] + feature_cols)
        
        logger.info(f"Training on {len(df):,} samples with {len(feature_cols)} features")
        
        # Prepare X and y
        X = df[feature_cols]
        y = df['target']
        
        # Check class distribution
        class_dist = y.value_counts()
        logger.info(f"Class distribution:\n{class_dist}")
        logger.info(f"Class balance: {class_dist[1] / len(y) * 100:.1f}% UP")
        
        # Split data (time-based split)
        split_idx = int(len(df) * (1 - Config.TEST_SIZE))
        
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]
        
        logger.info(f"Train set: {len(X_train):,} samples")
        logger.info(f"Test set: {len(X_test):,} samples")
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=Config.N_ESTIMATORS,
            max_depth=Config.MAX_DEPTH,
            min_samples_split=Config.MIN_SAMPLES_SPLIT,
            random_state=Config.RANDOM_STATE,
            n_jobs=-1,
            verbose=1
        )
        
        model.fit(X_train, y_train)
        
        logger.info("Model training completed")
        
        return model, X_test, y_test, feature_cols


def evaluate_model(model, X_test, y_test, feature_cols):
    """
    Evaluate model performance.
    """
    with PerformanceTimer("Model evaluation"):
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        metrics = ModelEvaluator.calculate_metrics(y_test, y_pred, y_pred_proba)
        
        # Print metrics
        ModelEvaluator.print_metrics(metrics)
        
        # Plot confusion matrix
        try:
            cm_plot = ModelEvaluator.plot_confusion_matrix(y_test, y_pred)
            cm_path = Config.MODELS_DIR / 'confusion_matrix.png'
            cm_plot.savefig(cm_path)
            logger.info(f"Saved confusion matrix to {cm_path}")
        except Exception as e:
            logger.warning(f"Could not save confusion matrix: {e}")
        
        # Plot feature importance
        try:
            fi_plot = ModelEvaluator.plot_feature_importance(model, feature_cols)
            if fi_plot:
                fi_path = Config.MODELS_DIR / 'feature_importance.png'
                fi_plot.savefig(fi_path)
                logger.info(f"Saved feature importance to {fi_path}")
        except Exception as e:
            logger.warning(f"Could not save feature importance: {e}")
        
        return metrics


def save_model(model, feature_cols, metrics):
    """
    Save trained model and metadata.
    """
    with PerformanceTimer("Saving model"):
        # Save model
        model_path = Config.get_model_file(f'{Config.MODEL_NAME}_{Config.MODEL_VERSION}.pkl')
        joblib.dump(model, model_path)
        logger.info(f"Saved model to {model_path}")
        
        # Save feature columns
        features_path = Config.get_model_file(f'{Config.MODEL_NAME}_{Config.MODEL_VERSION}_features.pkl')
        joblib.dump(feature_cols, features_path)
        logger.info(f"Saved feature columns to {features_path}")
        
        # Save metadata
        metadata = {
            'model_name': Config.MODEL_NAME,
            'model_version': Config.MODEL_VERSION,
            'trained_at': pd.Timestamp.now().isoformat(),
            'n_estimators': Config.N_ESTIMATORS,
            'max_depth': Config.MAX_DEPTH,
            'min_samples_split': Config.MIN_SAMPLES_SPLIT,
            'metrics': metrics,
            'features': feature_cols
        }
        
        metadata_path = Config.get_model_file(f'{Config.MODEL_NAME}_{Config.MODEL_VERSION}_metadata.pkl')
        joblib.dump(metadata, metadata_path)
        logger.info(f"Saved metadata to {metadata_path}")


def main():
    """Main training pipeline."""
    setup_logging()
    Config.validate()
    
    logger.info("="*60)
    logger.info("STOCK DIRECTION PREDICTION - MODEL TRAINING")
    logger.info("="*60)
    
    try:
        # Prepare data
        features_df = prepare_training_data()
        
        # Train model
        model, X_test, y_test, feature_cols = train_model(features_df)
        
        # Evaluate model
        metrics = evaluate_model(model, X_test, y_test, feature_cols)
        
        # Save model
        save_model(model, feature_cols, metrics)
        
        logger.info("="*60)
        logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
