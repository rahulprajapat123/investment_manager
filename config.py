"""
Configuration management for the Investment Platform.
"""

import os
from typing import Optional
from pathlib import Path

class Config:
    """Application configuration."""
    
    # Project Settings
    PROJECT_ROOT = Path(__file__).parent
    DATA_DIR = PROJECT_ROOT / 'data'
    MODELS_DIR = PROJECT_ROOT / 'models_output'
    
    # GCP Settings (for cloud deployment)
    GCP_PROJECT_ID: str = os.getenv('GCP_PROJECT_ID', 'investment-platform-demo')
    GCP_REGION: str = os.getenv('GCP_REGION', 'us-central1')
    
    # BigQuery Settings
    DATASET_ID: str = 'investment_platform'
    
    # API Keys (use Secret Manager in production!)
    NEWS_API_KEY: Optional[str] = os.getenv('NEWS_API_KEY', 'demo-key-12345')
    ALPHA_VANTAGE_KEY: Optional[str] = os.getenv('ALPHA_VANTAGE_KEY', 'demo-key-67890')
    
    # Feature Flags
    ENABLE_ML_PREDICTIONS: bool = os.getenv('ENABLE_ML', 'true').lower() == 'true'
    ENABLE_NOTIFICATIONS: bool = os.getenv('ENABLE_NOTIF', 'true').lower() == 'true'
    USE_LOCAL_DATA: bool = os.getenv('USE_LOCAL_DATA', 'true').lower() == 'true'
    
    # Performance Settings
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '10'))
    QUERY_TIMEOUT: int = int(os.getenv('QUERY_TIMEOUT', '60'))
    
    # Model Settings
    MODEL_NAME: str = 'stock_direction_classifier'
    MODEL_VERSION: str = 'v1'
    
    # ML Hyperparameters
    N_ESTIMATORS: int = 200
    MAX_DEPTH: int = 15
    MIN_SAMPLES_SPLIT: int = 100
    TEST_SIZE: float = 0.2
    RANDOM_STATE: int = 42
    
    # Feature Engineering
    LOOKBACK_DAYS: int = 30
    VOLATILITY_WINDOW: int = 30
    SMA_WINDOWS: list = [50, 200]
    
    # API Settings
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8080'))
    DEBUG_MODE: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.DATA_DIR.exists():
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        if not cls.MODELS_DIR.exists():
            cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        print("✓ Configuration validated")
    
    @classmethod
    def get_data_file(cls, filename: str) -> Path:
        """Get full path to data file."""
        return cls.DATA_DIR / filename
    
    @classmethod
    def get_model_file(cls, filename: str) -> Path:
        """Get full path to model file."""
        return cls.MODELS_DIR / filename
