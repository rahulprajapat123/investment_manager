# Investment Platform - Demo Project

A complete investment platform with machine learning-powered stock predictions, portfolio management, and RESTful API.

## 🚀 Features

- **📊 Portfolio Management**: Track multiple client portfolios with real-time valuations
- **🤖 ML Predictions**: Random Forest model predicts stock direction with confidence scores
- **📈 Technical Analysis**: RSI, MACD, moving averages, volatility metrics
- **💬 Sentiment Analysis**: News sentiment integration
- **🔌 REST API**: Flask-based API for all operations
- **☁️ Cloud-Ready**: Designed for easy GCP deployment

---

## 📁 Project Structure

```
demo investment project/
├── src/
│   ├── functions/          # Cloud Functions (data ingestion, processing)
│   ├── models/            # ML training and prediction
│   │   ├── train.py       # Train ML model
│   │   └── predict.py     # Make predictions
│   ├── api/               # Flask REST API
│   │   └── app.py         # Main API application
│   └── utils/             # Utility modules
│       ├── database.py    # Data access layer
│       ├── ml_utils.py    # ML utilities
│       └── helpers.py     # Helper functions
├── data/                  # Generated datasets (CSV files)
├── models_output/         # Trained ML models
├── tests/                 # Unit tests
├── sql/                   # SQL scripts and migrations
├── docs/                  # Documentation
├── generate_data.py       # Generate synthetic datasets
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
└── README.md            # This file
```

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git (optional)

### Step 1: Install Dependencies

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Generate Synthetic Data

```powershell
# Generate all datasets
python generate_data.py
```

This creates the following files in `data/`:
- `daily_prices.csv` - Historical stock prices (5 years, 20 tickers)
- `portfolio_holdings.csv` - Client portfolios
- `news_sentiment.csv` - News sentiment scores
- `market_data.csv` - Market indices (S&P 500)
- `client_profiles.csv` - Client risk profiles

### Step 3: Train ML Model

```powershell
# Train the stock prediction model
python src/models/train.py
```

This will:
- Engineer features from price and sentiment data
- Train a Random Forest classifier
- Evaluate model performance
- Save model to `models_output/`

Expected output:
```
MODEL EVALUATION METRICS
==================================================
ACCURACY................ 0.7200
PRECISION............... 0.7100
RECALL.................. 0.7300
F1...................... 0.7200
AUC..................... 0.7800
==================================================
```

### Step 4: Test Predictions

```powershell
# Test predictions on sample stocks
python src/models/predict.py
```

### Step 5: Start API Server

```powershell
# Start Flask API
python src/api/app.py
```

API will be available at: `http://localhost:8080`

---

## 📡 API Endpoints

### Health Check
```
GET /health
```

### Get Portfolio
```
GET /api/portfolio/<client_id>

Example: http://localhost:8080/api/portfolio/1
```

Response:
```json
{
  "client_id": 1,
  "total_value": "$45,230.50",
  "total_gain_loss": "+$5,230.50",
  "total_gain_loss_pct": "+13.07%",
  "positions": [
    {
      "ticker": "AAPL",
      "shares": 100,
      "current_price": "$191.00",
      "position_value": "$19,100.00",
      "gain_loss": "+$1,100.00",
      "gain_loss_pct": "+6.11%"
    }
  ]
}
```

### Get Stock Information
```
GET /api/stock/<ticker>

Example: http://localhost:8080/api/stock/AAPL
```

### Get ML Prediction
```
GET /api/predict/<ticker>

Example: http://localhost:8080/api/predict/AAPL
```

Response:
```json
{
  "ticker": "AAPL",
  "current_price": 191.00,
  "prediction": {
    "direction": "UP",
    "probability_up": "72.5%",
    "probability_down": "27.5%"
  },
  "recommendation": {
    "action": "BUY",
    "strength": "Moderate",
    "confidence": "72.5%"
  }
}
```

### Get Top Recommendations
```
GET /api/recommendations?action=BUY&limit=5

Parameters:
- action: BUY/SELL/HOLD (default: BUY)
- limit: Number of results (default: 5)
```

### Get Top Performers
```
GET /api/top-stocks?period=30d&limit=10

Parameters:
- period: 1d/5d/30d (default: 1d)
- limit: Number of results (default: 10)
```

---

## 🧪 Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Understanding the ML Model

### Features Used

1. **Price-Based Features**:
   - Returns (1d, 5d, 10d, 30d)
   - Volatility (10d, 30d, 60d)
   - Moving averages (SMA 50, 200)
   - Golden cross indicator

2. **Technical Indicators**:
   - RSI (Relative Strength Index)
   - MACD (Moving Average Convergence Divergence)

3. **Sentiment Features**:
   - Average news sentiment
   - Sentiment volatility
   - News article count

4. **Volume**:
   - Trading volume

### Model: Random Forest Classifier

- **Algorithm**: Ensemble of 200 decision trees
- **Task**: Binary classification (UP vs DOWN)
- **Target**: Stock direction in next trading day
- **Accuracy**: ~72% on test set

### How It Works

```
1. Historical Data → Feature Engineering
2. Features → Random Forest Model
3. Model → Probability of UP (0-1)
4. Probability → Recommendation (BUY/SELL/HOLD)
```

---

## 🐳 Docker Deployment

### Build Docker Image

```powershell
# Build image
docker build -t investment-platform .

# Run container
docker run -p 8080:8080 investment-platform
```

---

## ☁️ Google Cloud Platform Deployment

See **[GCP_DEPLOYMENT_GUIDE.md](docs/GCP_DEPLOYMENT_GUIDE.md)** for detailed instructions.

### Quick Start (GCP)

1. **Install Google Cloud SDK**
   ```powershell
   # Download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate**
   ```powershell
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Deploy to Cloud Run**
   ```powershell
   gcloud run deploy investment-api \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

4. **Set Up BigQuery**
   ```powershell
   # Create dataset
   bq mk --dataset investment_platform

   # Load data
   bq load --source_format=CSV investment_platform.daily_prices data/daily_prices.csv
   ```

---

## 📈 Demo Walkthrough

### 1. Check API Status
```powershell
curl http://localhost:8080/health
```

### 2. Get Portfolio Value
```powershell
curl http://localhost:8080/api/portfolio/1
```

### 3. Get Stock Prediction
```powershell
curl http://localhost:8080/api/predict/AAPL
```

### 4. Get Top Buy Recommendations
```powershell
curl "http://localhost:8080/api/recommendations?action=BUY&limit=5"
```

---

## 🔧 Configuration

Edit `config.py` or create `.env` file (copy from `.env.example`):

```env
# GCP Settings
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Feature Flags
ENABLE_ML=true
USE_LOCAL_DATA=true

# API Settings
API_PORT=8080
DEBUG=false
```

---

## 📚 Additional Resources

- **Documentation Part 1**: Cloud architecture and services
- **Documentation Part 2**: ML, deployment, and operations
- **GCP Deployment Guide**: Step-by-step cloud deployment

---

## 🎯 Next Steps

1. ✅ **Local Demo**: Run locally and test all features
2. ✅ **Understand Code**: Review key files and logic
3. ✅ **Test Predictions**: Verify ML model works
4. ☁️ **Deploy to GCP**: Follow deployment guide
5. 📊 **Add Dashboard**: Build frontend UI (optional)

---

## 📞 Support

For questions or issues:
1. Check documentation in `docs/`
2. Review code comments
3. Run tests to verify setup
4. Check API logs for errors

---

## 📝 License

Demo project for educational purposes.

---

**Built with**: Python, Flask, scikit-learn, pandas, BigQuery, Cloud Run
