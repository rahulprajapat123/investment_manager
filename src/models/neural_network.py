"""
Neural Network models for stock prediction.
Implements LSTM and Feed-Forward Neural Networks using TensorFlow/Keras.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database
from src.utils.ml_utils import FeatureEngineer

logger = logging.getLogger(__name__)

# Try to import TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, models, callbacks
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. Neural network features disabled.")


class LSTMPredictor:
    """
    Long Short-Term Memory (LSTM) neural network for time series prediction.
    Captures temporal dependencies in stock price movements.
    """
    
    def __init__(
        self,
        sequence_length: int = 60,
        lstm_units: List[int] = [128, 64],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001
    ):
        """
        Initialize LSTM predictor.
        
        Args:
            sequence_length: Number of time steps to look back
            lstm_units: List of LSTM layer units
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM. Install with: pip install tensorflow")
        
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self.db = get_database()
    
    def build_model(self, n_features: int) -> models.Sequential:
        """
        Build LSTM model architecture.
        
        Args:
            n_features: Number of input features
            
        Returns:
            Compiled Keras model
        """
        model = models.Sequential()
        
        # First LSTM layer
        model.add(layers.LSTM(
            self.lstm_units[0],
            return_sequences=True if len(self.lstm_units) > 1 else False,
            input_shape=(self.sequence_length, n_features)
        ))
        model.add(layers.Dropout(self.dropout_rate))
        
        # Additional LSTM layers
        for i, units in enumerate(self.lstm_units[1:]):
            return_seq = i < len(self.lstm_units) - 2
            model.add(layers.LSTM(units, return_sequences=return_seq))
            model.add(layers.Dropout(self.dropout_rate))
        
        # Dense layers
        model.add(layers.Dense(32, activation='relu'))
        model.add(layers.Dropout(self.dropout_rate))
        
        # Output layer (binary classification: up/down)
        model.add(layers.Dense(1, activation='sigmoid'))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
        )
        
        return model
    
    def prepare_sequences(
        self,
        data: pd.DataFrame,
        target_column: str = 'target'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequential data for LSTM.
        
        Args:
            data: DataFrame with features and target
            target_column: Name of target column
            
        Returns:
            Tuple of (X_sequences, y_targets)
        """
        from sklearn.preprocessing import StandardScaler
        
        # Separate features and target
        feature_cols = [col for col in data.columns if col not in [target_column, 'date', 'ticker']]
        features = data[feature_cols].values
        targets = data[target_column].values
        
        # Scale features
        if self.scaler is None:
            self.scaler = StandardScaler()
            features_scaled = self.scaler.fit_transform(features)
        else:
            features_scaled = self.scaler.transform(features)
        
        # Create sequences
        X_sequences = []
        y_targets = []
        
        for i in range(self.sequence_length, len(features_scaled)):
            X_sequences.append(features_scaled[i-self.sequence_length:i])
            y_targets.append(targets[i])
        
        return np.array(X_sequences), np.array(y_targets)
    
    def train(
        self,
        tickers: List[str],
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2,
        early_stopping_patience: int = 10
    ) -> Dict:
        """
        Train LSTM model on multiple tickers.
        
        Args:
            tickers: List of stock tickers
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Validation data split ratio
            early_stopping_patience: Patience for early stopping
            
        Returns:
            Training history
        """
        # Collect data for all tickers
        all_data = []
        
        for ticker in tickers:
            # Load price data
            prices_df = self.db.load_daily_prices(ticker=ticker)
            if prices_df.empty:
                continue
            
            # Load sentiment
            sentiment_df = self.db.load_news_sentiment(ticker=ticker, days=365*2)
            
            # Engineer features
            features_df = FeatureEngineer.engineer_all_features(prices_df, sentiment_df)
            
            # Create target: 1 if next day return > 0, else 0
            features_df['future_return'] = features_df['return_1d'].shift(-1)
            features_df['target'] = (features_df['future_return'] > 0).astype(int)
            features_df = features_df.dropna()
            
            all_data.append(features_df)
        
        if not all_data:
            raise ValueError("No data available for training")
        
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Prepare sequences
        X, y = self.prepare_sequences(combined_data, target_column='target')
        
        logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
        
        # Build model
        n_features = X.shape[2]
        self.model = self.build_model(n_features)
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=early_stopping_patience,
            restore_best_weights=True
        )
        
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001
        )
        
        # Train
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        # Save model
        model_path = Config.get_model_file('lstm_model.h5')
        self.model.save(model_path)
        logger.info(f"Model saved to {model_path}")
        
        return {
            'loss': history.history['loss'][-1],
            'accuracy': history.history['accuracy'][-1],
            'val_loss': history.history['val_loss'][-1],
            'val_accuracy': history.history['val_accuracy'][-1],
            'epochs_trained': len(history.history['loss'])
        }
    
    def predict(self, ticker: str, n_days: int = 1) -> Dict:
        """
        Predict future stock movement.
        
        Args:
            ticker: Stock ticker
            n_days: Number of days to predict ahead
            
        Returns:
            Prediction results
        """
        if self.model is None:
            # Try to load saved model
            model_path = Config.get_model_file('lstm_model.h5')
            if model_path.exists():
                self.model = keras.models.load_model(model_path)
            else:
                raise ValueError("Model not trained. Call train() first.")
        
        # Load recent data
        prices_df = self.db.load_daily_prices(ticker=ticker)
        sentiment_df = self.db.load_news_sentiment(ticker=ticker, days=90)
        
        # Engineer features
        features_df = FeatureEngineer.engineer_all_features(prices_df, sentiment_df)
        features_df['target'] = 0  # Dummy target
        
        # Get last sequence
        X, _ = self.prepare_sequences(features_df, target_column='target')
        
        if len(X) == 0:
            raise ValueError(f"Insufficient data for {ticker}")
        
        last_sequence = X[-1:]
        
        # Predict
        prediction_prob = self.model.predict(last_sequence, verbose=0)[0][0]
        
        return {
            'ticker': ticker,
            'prediction': 'UP' if prediction_prob > 0.5 else 'DOWN',
            'probability_up': float(prediction_prob),
            'probability_down': float(1 - prediction_prob),
            'confidence': float(max(prediction_prob, 1 - prediction_prob)),
            'model': 'LSTM'
        }


class FeedForwardNN:
    """
    Feed-Forward Neural Network for stock prediction.
    Simpler architecture for non-sequential feature patterns.
    """
    
    def __init__(
        self,
        hidden_layers: List[int] = [256, 128, 64],
        dropout_rate: float = 0.3,
        learning_rate: float = 0.001
    ):
        """
        Initialize Feed-Forward NN.
        
        Args:
            hidden_layers: List of hidden layer units
            dropout_rate: Dropout rate for regularization
            learning_rate: Learning rate for optimizer
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required. Install with: pip install tensorflow")
        
        self.hidden_layers = hidden_layers
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = None
        self.db = get_database()
    
    def build_model(self, n_features: int) -> models.Sequential:
        """
        Build Feed-Forward NN architecture.
        
        Args:
            n_features: Number of input features
            
        Returns:
            Compiled Keras model
        """
        model = models.Sequential()
        
        # Input layer
        model.add(layers.Dense(
            self.hidden_layers[0],
            activation='relu',
            input_shape=(n_features,)
        ))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(self.dropout_rate))
        
        # Hidden layers
        for units in self.hidden_layers[1:]:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.BatchNormalization())
            model.add(layers.Dropout(self.dropout_rate))
        
        # Output layer
        model.add(layers.Dense(1, activation='sigmoid'))
        
        # Compile
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        
        return model
    
    def train(
        self,
        tickers: List[str],
        epochs: int = 100,
        batch_size: int = 64,
        validation_split: float = 0.2
    ) -> Dict:
        """
        Train Feed-Forward NN.
        
        Args:
            tickers: List of stock tickers
            epochs: Number of training epochs
            batch_size: Batch size
            validation_split: Validation split ratio
            
        Returns:
            Training metrics
        """
        from sklearn.preprocessing import StandardScaler
        
        # Collect data
        all_features = []
        all_targets = []
        
        for ticker in tickers:
            prices_df = self.db.load_daily_prices(ticker=ticker)
            if prices_df.empty:
                continue
            
            sentiment_df = self.db.load_news_sentiment(ticker=ticker, days=365*2)
            features_df = FeatureEngineer.engineer_all_features(prices_df, sentiment_df)
            
            # Create target
            features_df['future_return'] = features_df['return_1d'].shift(-1)
            features_df['target'] = (features_df['future_return'] > 0).astype(int)
            features_df = features_df.dropna()
            
            # Get feature columns
            feature_cols = [col for col in features_df.columns 
                           if col not in ['target', 'date', 'ticker', 'future_return']]
            
            all_features.append(features_df[feature_cols])
            all_targets.append(features_df['target'])
        
        if not all_features:
            raise ValueError("No data available")
        
        # Combine
        X = pd.concat(all_features, ignore_index=True).values
        y = pd.concat(all_targets, ignore_index=True).values
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Build and train model
        self.model = self.build_model(X_scaled.shape[1])
        
        early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
        reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7)
        
        history = self.model.fit(
            X_scaled, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        # Save
        model_path = Config.get_model_file('ffnn_model.h5')
        self.model.save(model_path)
        
        return {
            'accuracy': history.history['accuracy'][-1],
            'val_accuracy': history.history['val_accuracy'][-1],
            'precision': history.history['precision'][-1],
            'recall': history.history['recall'][-1]
        }


def main():
    """Demo neural network training."""
    from src.utils.helpers import setup_logging
    
    setup_logging()
    
    if not TENSORFLOW_AVAILABLE:
        print("TensorFlow not installed. Please install with: pip install tensorflow")
        return
    
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    print("\n" + "="*60)
    print("FEED-FORWARD NEURAL NETWORK")
    print("="*60 + "\n")
    
    ffnn = FeedForwardNN(hidden_layers=[128, 64, 32])
    metrics = ffnn.train(tickers, epochs=50, batch_size=64)
    
    print(f"Training Accuracy: {metrics['accuracy']:.2%}")
    print(f"Validation Accuracy: {metrics['val_accuracy']:.2%}")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall: {metrics['recall']:.2%}")
    
    print("\n" + "="*60)
    print("LSTM NEURAL NETWORK")
    print("="*60 + "\n")
    
    lstm = LSTMPredictor(sequence_length=30, lstm_units=[64, 32])
    lstm_metrics = lstm.train(tickers, epochs=30, batch_size=32)
    
    print(f"Training Accuracy: {lstm_metrics['accuracy']:.2%}")
    print(f"Validation Accuracy: {lstm_metrics['val_accuracy']:.2%}")
    print(f"Epochs Trained: {lstm_metrics['epochs_trained']}")
    
    # Test prediction
    print("\nTesting LSTM Prediction on AAPL:")
    prediction = lstm.predict('AAPL')
    print(f"Prediction: {prediction['prediction']}")
    print(f"Confidence: {prediction['confidence']:.2%}")


if __name__ == '__main__':
    main()
