# Google Cloud Platform Deployment Guide

Complete step-by-step guide to deploy the Investment Platform on GCP.

---

## 📋 Prerequisites

- Google Cloud account with billing enabled
- Project deployed locally and working
- Basic understanding of cloud services

---

## 🎯 Deployment Overview

```
Local Development
    ↓
GCP Project Setup
    ↓
Cloud Storage (Data & Models)
    ↓
BigQuery (Database)
    ↓
Cloud Run (API)
    ↓
Cloud Functions (Scheduled Jobs)
    ↓
Cloud Scheduler (Automation)
    ↓
Monitoring & Logging
```

---

## Step 1: GCP Project Setup

### 1.1 Install Google Cloud SDK

```powershell
# Download and install from:
# https://cloud.google.com/sdk/docs/install

# Verify installation
gcloud --version
```

### 1.2 Create GCP Project

```powershell
# Login to Google Cloud
gcloud auth login

# Create new project
gcloud projects create investment-platform-demo --name="Investment Platform"

# Set as active project
gcloud config set project investment-platform-demo

# Enable billing (do this in Console)
# https://console.cloud.google.com/billing
```

### 1.3 Enable Required APIs

```powershell
# Enable all necessary APIs
gcloud services enable \
  bigquery.googleapis.com \
  storage.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  secretmanager.googleapis.com
```

**What this does**: Activates the GCP services we'll use (BigQuery for database, Cloud Run for API, etc.)

---

## Step 2: Cloud Storage Setup

### 2.1 Create Storage Buckets

```powershell
# Bucket for data files
gsutil mb -l us-central1 gs://investment-platform-data

# Bucket for ML models
gsutil mb -l us-central1 gs://investment-platform-models

# Bucket for backups
gsutil mb -l us-central1 gs://investment-platform-backups
```

**What this does**: Creates storage locations (like folders in the cloud) for your data, models, and backups.

### 2.2 Upload Data and Models

```powershell
# Upload data files
gsutil -m cp data/*.csv gs://investment-platform-data/

# Upload trained model
gsutil -m cp models_output/*.pkl gs://investment-platform-models/

# Verify upload
gsutil ls gs://investment-platform-data/
gsutil ls gs://investment-platform-models/
```

**What this does**: Copies your local CSV files and trained ML model to cloud storage.

---

## Step 3: BigQuery Database Setup

### 3.1 Create Dataset

```powershell
# Create BigQuery dataset
bq mk --dataset --location=US investment_platform

# Verify
bq ls
```

**What this does**: Creates a "database" in BigQuery called `investment_platform`.

### 3.2 Create Tables and Load Data

```powershell
# Load daily prices
bq load \
  --source_format=CSV \
  --autodetect \
  investment_platform.daily_prices \
  gs://investment-platform-data/daily_prices.csv

# Load portfolio holdings
bq load \
  --source_format=CSV \
  --autodetect \
  investment_platform.portfolio_holdings \
  gs://investment-platform-data/portfolio_holdings.csv

# Load news sentiment
bq load \
  --source_format=CSV \
  --autodetect \
  investment_platform.news_sentiment \
  gs://investment-platform-data/news_sentiment.csv

# Load market data
bq load \
  --source_format=CSV \
  --autodetect \
  investment_platform.market_data \
  gs://investment-platform-data/market_data.csv

# Load client profiles
bq load \
  --source_format=CSV \
  --autodetect \
  investment_platform.client_profiles \
  gs://investment-platform-data/client_profiles.csv
```

**What this does**: Creates tables in BigQuery and loads your CSV data into them.

### 3.3 Verify Data

```powershell
# List tables
bq ls investment_platform

# Query data
bq query --use_legacy_sql=false \
'SELECT ticker, COUNT(*) as count 
 FROM investment_platform.daily_prices 
 GROUP BY ticker 
 LIMIT 10'
```

**What this does**: Checks that your data loaded correctly.

### 3.4 Optimize Tables (Partitioning & Clustering)

```sql
-- Create optimized daily_prices table
CREATE OR REPLACE TABLE investment_platform.daily_prices_optimized
PARTITION BY date
CLUSTER BY ticker
AS
SELECT * FROM investment_platform.daily_prices;

-- Create optimized news_sentiment table
CREATE OR REPLACE TABLE investment_platform.news_sentiment_optimized
PARTITION BY date
CLUSTER BY ticker
AS
SELECT * FROM investment_platform.news_sentiment;
```

**What this does**: Makes queries faster and cheaper by organizing data efficiently.

---

## Step 4: Deploy API to Cloud Run

### 4.1 Update Configuration

Edit `config.py` to use BigQuery in production:

```python
# In config.py, add:
import os

USE_LOCAL_DATA = os.getenv('USE_LOCAL_DATA', 'false').lower() == 'true'
```

### 4.2 Build and Deploy

```powershell
# Deploy to Cloud Run (builds automatically)
gcloud run deploy investment-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars USE_LOCAL_DATA=false,GCP_PROJECT_ID=investment-platform-demo
```

**What this does**: 
1. Packages your code into a container
2. Uploads it to Google Cloud
3. Runs it as a web service
4. Gives you a URL to access it

### 4.3 Get Service URL

```powershell
# Get the deployed URL
gcloud run services describe investment-api \
  --region us-central1 \
  --format 'value(status.url)'
```

Output: `https://investment-api-xxxxx-uc.a.run.app`

### 4.4 Test Deployed API

```powershell
# Test health endpoint
curl https://investment-api-xxxxx-uc.a.run.app/health

# Test stock endpoint
curl https://investment-api-xxxxx-uc.a.run.app/api/stock/AAPL

# Test prediction endpoint
curl https://investment-api-xxxxx-uc.a.run.app/api/predict/AAPL
```

**What this does**: Verifies your API is working in the cloud.

---

## Step 5: Set Up Cloud Functions

### 5.1 Create Data Ingestion Function

Create `src/functions/ingest_data/main.py`:

```python
from google.cloud import bigquery
import functions_framework

@functions_framework.http
def ingest_market_data(request):
    """
    Fetch and ingest latest market data.
    Triggered by Cloud Scheduler daily.
    """
    try:
        # Your data ingestion logic here
        # For demo, just log
        print("Ingesting market data...")
        
        return {'status': 'success', 'message': 'Data ingested'}, 200
    
    except Exception as e:
        print(f"Error: {e}")
        return {'status': 'error', 'message': str(e)}, 500
```

Create `src/functions/ingest_data/requirements.txt`:

```
google-cloud-bigquery==3.14.1
functions-framework==3.5.0
```

### 5.2 Deploy Cloud Function

```powershell
# Navigate to function directory
cd src/functions/ingest_data

# Deploy function
gcloud functions deploy ingest-market-data \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --trigger-http \
  --entry-point ingest_market_data \
  --memory 512MB \
  --timeout 300s \
  --allow-unauthenticated

# Navigate back
cd ../../..
```

**What this does**: Creates a serverless function that can fetch and process market data.

---

## Step 6: Set Up Cloud Scheduler

### 6.1 Create Daily Data Refresh Job

```powershell
# Create job to run daily at 5:00 PM EST
gcloud scheduler jobs create http market-data-daily \
  --location us-central1 \
  --schedule "0 17 * * 1-5" \
  --time-zone "America/New_York" \
  --uri "https://us-central1-investment-platform-demo.cloudfunctions.net/ingest-market-data" \
  --http-method GET
```

**What this does**: Automatically runs data ingestion every weekday at 5 PM (after market close).

**Cron Schedule Explained**:
```
0 17 * * 1-5
│ │  │ │ └─ Days of week (1-5 = Monday-Friday)
│ │  │ └─── Months (every month)
│ │  └───── Days of month (every day)
│ └──────── Hour (17 = 5 PM)
└────────── Minute (0 = on the hour)
```

### 6.2 Create Weekly Model Retraining Job

```powershell
# Create job to retrain model weekly (Sunday 2 AM)
gcloud scheduler jobs create http model-retrain-weekly \
  --location us-central1 \
  --schedule "0 2 * * 0" \
  --time-zone "America/New_York" \
  --uri "YOUR_RETRAINING_FUNCTION_URL" \
  --http-method GET
```

### 6.3 Test Scheduler Jobs

```powershell
# Manually trigger job
gcloud scheduler jobs run market-data-daily --location us-central1

# Check execution history
gcloud scheduler jobs describe market-data-daily --location us-central1
```

---

## Step 7: Set Up Monitoring & Alerts

### 7.1 Create Alert Policy for Errors

Go to Cloud Console → Monitoring → Alerting → Create Policy

Or use gcloud:

```powershell
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="High API Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

### 7.2 Set Up Logging

```powershell
# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Create log sink to BigQuery (for analysis)
gcloud logging sinks create investment-api-logs \
  bigquery.googleapis.com/projects/investment-platform-demo/datasets/logs \
  --log-filter='resource.type="cloud_run_revision"'
```

**What this does**: Saves all API logs to BigQuery so you can analyze them.

---

## Step 8: Security Setup

### 8.1 Store API Keys in Secret Manager

```powershell
# Create secret for News API key
echo -n "your-news-api-key" | gcloud secrets create NEWS_API_KEY --data-file=-

# Create secret for Alpha Vantage key
echo -n "your-alpha-vantage-key" | gcloud secrets create ALPHA_VANTAGE_KEY --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding NEWS_API_KEY \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 8.2 Update Cloud Run to Use Secrets

```powershell
# Redeploy with secrets
gcloud run deploy investment-api \
  --source . \
  --region us-central1 \
  --update-secrets NEWS_API_KEY=NEWS_API_KEY:latest,ALPHA_VANTAGE_KEY=ALPHA_VANTAGE_KEY:latest
```

---

## Step 9: Cost Optimization

### 9.1 Set Up Budget Alerts

Go to: Cloud Console → Billing → Budgets & Alerts

1. Click "CREATE BUDGET"
2. Set monthly budget (e.g., $50)
3. Set alerts at 50%, 90%, 100%
4. Add email notification

### 9.2 Optimize BigQuery Costs

```sql
-- Set up partition expiration (auto-delete old data)
ALTER TABLE investment_platform.daily_prices_optimized
SET OPTIONS (
  partition_expiration_days = 1825  -- 5 years
);

-- Set up lifecycle policy for Cloud Storage
gsutil lifecycle set lifecycle.json gs://investment-platform-data/
```

Create `lifecycle.json`:

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
```

### 9.3 Set Cloud Run Autoscaling

```powershell
# Update Cloud Run with cost-optimized settings
gcloud run services update investment-api \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 5 \
  --cpu-throttling
```

**What this does**: 
- Scales to 0 when no requests (no cost!)
- Max 5 instances to prevent runaway costs
- Throttles CPU when idle to save money

---

## Step 10: Testing & Validation

### 10.1 End-to-End Test

```powershell
# Get your Cloud Run URL
$API_URL = "https://investment-api-xxxxx-uc.a.run.app"

# Test all endpoints
curl "$API_URL/health"
curl "$API_URL/api/portfolio/1"
curl "$API_URL/api/stock/AAPL"
curl "$API_URL/api/predict/AAPL"
curl "$API_URL/api/recommendations?action=BUY&limit=5"
```

### 10.2 Load Test (Optional)

```powershell
# Install Apache Bench
# Windows: Download from https://www.apachelounge.com/download/

# Run load test
ab -n 1000 -c 10 "$API_URL/health"
```

**What this does**: Sends 1000 requests with 10 concurrent users to test performance.

---

## 📊 Architecture Diagram

```
┌─────────────────┐
│   Cloud         │
│   Scheduler     │ ──> Triggers daily at 5 PM
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Cloud         │
│   Function      │ ──> Fetches market data
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   BigQuery      │ ──> Stores data
│   (Database)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Cloud Run     │ ──> Serves API
│   (API Server)  │ <── Client requests
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Cloud         │
│   Logging       │ ──> Monitors everything
└─────────────────┘
```

---

## 💰 Cost Estimate

**Monthly costs for moderate usage**:

- **Cloud Run**: $5-15 (free tier: 2 million requests)
- **BigQuery**: $10-30 (free tier: 1 TB queries, 10 GB storage)
- **Cloud Storage**: $1-5 (free tier: 5 GB)
- **Cloud Functions**: $2-10 (free tier: 2 million invocations)
- **Cloud Scheduler**: $0.10 per job

**Total**: ~$20-60/month (most features free with low usage)

---

## 🔍 Monitoring Dashboard

Access in Cloud Console:
1. Go to **Cloud Run** → Click your service → **METRICS** tab
2. View: Requests, Latency, Errors, Instance Count

Key metrics to watch:
- **Request count**: How many API calls
- **Latency (p95)**: 95% of requests complete in X ms
- **Error rate**: Should be < 1%
- **Instance count**: Number of servers running

---

## 🚨 Troubleshooting

### API Returns 500 Error

```powershell
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 10 --format json

# Check recent errors
gcloud logging read "severity=ERROR" --limit 10
```

### BigQuery Query Fails

```powershell
# Test query directly
bq query --use_legacy_sql=false \
'SELECT COUNT(*) FROM investment_platform.daily_prices'
```

### Cloud Function Not Triggering

```powershell
# Check scheduler job status
gcloud scheduler jobs describe market-data-daily --location us-central1

# Manually trigger
gcloud scheduler jobs run market-data-daily --location us-central1

# Check function logs
gcloud functions logs read ingest-market-data --limit 50
```

---

## 🎉 Success Checklist

- [ ] GCP project created and billing enabled
- [ ] All APIs enabled
- [ ] Data uploaded to Cloud Storage
- [ ] BigQuery tables created and populated
- [ ] Cloud Run API deployed and accessible
- [ ] Cloud Functions deployed
- [ ] Cloud Scheduler jobs created
- [ ] Monitoring and alerts set up
- [ ] Secrets stored in Secret Manager
- [ ] Budget alerts configured
- [ ] End-to-end testing completed

---

## 🔄 CI/CD Pipeline (Advanced)

For automated deployments, set up GitHub Actions:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - id: 'auth'
        uses: 'google-github-actions/auth@v1'
        with:
          credentials_json: '${{ secrets.GCP_SA_KEY }}'
      
      - name: 'Deploy to Cloud Run'
        uses: 'google-github-actions/deploy-cloudrun@v1'
        with:
          service: 'investment-api'
          region: 'us-central1'
          source: '.'
```

---

## 📚 Next Steps

1. **Monitor Performance**: Check Cloud Console daily
2. **Optimize Costs**: Review billing after 1 week
3. **Add Features**: Implement new endpoints
4. **Scale**: Increase max instances as needed
5. **Secure**: Add authentication (Firebase Auth)

---

**Congratulations! Your Investment Platform is now running on Google Cloud! 🎉**
