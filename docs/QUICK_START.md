# 🚀 Quick Start Guide - Investment Platform

Get up and running in 10 minutes!

---

## ⚡ Super Fast Setup

### 1️⃣ Install Dependencies (2 minutes)

```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2️⃣ Generate Data (1 minute)

```powershell
# Generate synthetic datasets
python generate_data.py
```

Output:
```
✓ Created daily_prices.csv with 24,680 rows
✓ Created portfolio_holdings.csv with 28 rows
✓ Created news_sentiment.csv with 450 rows
✓ Created market_data.csv with 1,260 rows
✓ Created client_profiles.csv with 5 rows
```

### 3️⃣ Train ML Model (3 minutes)

```powershell
# Train the prediction model
python src/models/train.py
```

Expected accuracy: ~72%

### 4️⃣ Start API (30 seconds)

```powershell
# Start Flask server
python src/api/app.py
```

Server starts at: `http://localhost:8080`

### 5️⃣ Test API (1 minute)

Open browser or use curl:

```powershell
# Health check
curl http://localhost:8080/health

# Get portfolio
curl http://localhost:8080/api/portfolio/1

# Get prediction
curl http://localhost:8080/api/predict/AAPL

# Get recommendations
curl http://localhost:8080/api/recommendations?action=BUY&limit=5
```

---

## 🎯 Common Tasks

### View Portfolio Performance

```powershell
curl http://localhost:8080/api/portfolio/1
```

### Get Stock Prediction

```powershell
curl http://localhost:8080/api/predict/MSFT
```

### Find Top Stocks

```powershell
# Top performers (30 days)
curl "http://localhost:8080/api/top-stocks?period=30d&limit=10"

# Top buy recommendations
curl "http://localhost:8080/api/recommendations?action=BUY"
```

---

## 🧪 Run Tests

```powershell
# Run all tests
pytest tests/ -v

# Check specific test
pytest tests/test_main.py::TestHelpers::test_validate_ticker -v
```

---

## 📊 View Model Performance

After training, check:

- `models_output/confusion_matrix.png` - Accuracy visualization
- `models_output/feature_importance.png` - Top features
- Console output - Metrics (Accuracy, Precision, Recall, F1)

---

## 🐛 Troubleshooting

### "Module not found" Error

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "File not found" Error

```powershell
# Generate data first
python generate_data.py
```

### API Won't Start

```powershell
# Check if port 8080 is already in use
# Stop other services using port 8080

# Or change port in config.py:
# API_PORT = 8081
```

### Model Not Loading

```powershell
# Train model first
python src/models/train.py

# Verify model file exists
dir models_output\
```

---

## 📱 API Endpoints Cheat Sheet

| Endpoint | Description | Example |
|----------|-------------|---------|
| `/health` | Check API status | `curl http://localhost:8080/health` |
| `/api/portfolio/<id>` | Get portfolio | `curl http://localhost:8080/api/portfolio/1` |
| `/api/stock/<ticker>` | Get stock info | `curl http://localhost:8080/api/stock/AAPL` |
| `/api/predict/<ticker>` | ML prediction | `curl http://localhost:8080/api/predict/AAPL` |
| `/api/recommendations` | Top picks | `curl http://localhost:8080/api/recommendations` |
| `/api/top-stocks` | Top performers | `curl http://localhost:8080/api/top-stocks` |

---

## 🎓 Demo for Client

1. **Show Portfolio Dashboard**
   ```powershell
   curl http://localhost:8080/api/portfolio/1
   ```
   *"Here's a client's portfolio with real-time valuations"*

2. **Demonstrate ML Predictions**
   ```powershell
   curl http://localhost:8080/api/predict/AAPL
   ```
   *"Our ML model predicts stock direction with 72% accuracy"*

3. **Show Recommendations**
   ```powershell
   curl http://localhost:8080/api/recommendations?action=BUY&limit=5
   ```
   *"Top 5 stocks to buy based on ML analysis"*

4. **Explain Cloud Deployment**
   *"This runs locally now, but deploys to Google Cloud in minutes"*

---

## ☁️ Quick GCP Deployment

If client wants cloud demo immediately:

```powershell
# 1. Login to GCP
gcloud auth login

# 2. Set project
gcloud config set project YOUR_PROJECT_ID

# 3. Deploy (5 minutes)
gcloud run deploy investment-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

Get public URL instantly!

---

## 📈 Next Steps After Demo

1. ✅ Client likes it? → **Deploy to GCP** (see GCP_DEPLOYMENT_GUIDE.md)
2. 🎨 Want frontend? → **Build React dashboard**
3. 📊 More features? → **Add sentiment analysis, risk metrics**
4. 🔐 Production ready? → **Add authentication, monitoring**

---

## 💡 Tips

- **Demo Tip**: Have both terminal (for commands) and browser (for results) visible
- **Performance**: First prediction is slow (model loading), subsequent ones are fast
- **Data**: Refresh data anytime by running `python generate_data.py` again
- **Costs**: Local = $0, GCP = ~$20-50/month with free tier

---

## 🆘 Need Help?

1. Check `README.md` for full documentation
2. Review `docs/GCP_DEPLOYMENT_GUIDE.md` for cloud deployment
3. Run `pytest tests/ -v` to verify everything works
4. Check API logs in console for error details

---

**Ready to impress your client! 💪**
