# Google Cloud Run Deployment Script
# Run this script to deploy to Google Cloud Run

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Investment Analysis - GCP Deployment" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ID = Read-Host "Enter your GCP Project ID"
$SERVICE_NAME = "investment-analysis"
$REGION = "us-central1"

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project ID: $PROJECT_ID"
Write-Host "  Service Name: $SERVICE_NAME"
Write-Host "  Region: $REGION"
Write-Host ""

$confirm = Read-Host "Continue with deployment? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Deployment cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Step 1: Setting GCP project..." -ForegroundColor Green
gcloud config set project $PROJECT_ID

Write-Host ""
Write-Host "Step 2: Enabling required APIs..." -ForegroundColor Green
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

Write-Host ""
Write-Host "Step 3: Building and deploying to Cloud Run..." -ForegroundColor Green
gcloud run deploy $SERVICE_NAME `
    --source . `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --port 8080 `
    --max-instances 10

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your application is now live!" -ForegroundColor Green
Write-Host "View service details:" -ForegroundColor Yellow
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
