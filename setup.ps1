# Investment Platform - Complete Setup Script
# Run this to set up everything automatically

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INVESTMENT PLATFORM - SETUP SCRIPT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Step 2: Create virtual environment
Write-Host ""
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate virtual environment and install dependencies
Write-Host ""
Write-Host "[3/6] Installing dependencies..." -ForegroundColor Yellow
.\venv\Scripts\activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Step 4: Generate data
Write-Host ""
Write-Host "[4/6] Generating synthetic datasets..." -ForegroundColor Yellow
if (Test-Path "data\daily_prices.csv") {
    Write-Host "✓ Data already exists (skipping generation)" -ForegroundColor Green
} else {
    python generate_data.py
    Write-Host "✓ Data generated successfully" -ForegroundColor Green
}

# Step 5: Train model
Write-Host ""
Write-Host "[5/6] Training ML model..." -ForegroundColor Yellow
if (Test-Path "models_output\stock_direction_classifier_v1.pkl") {
    Write-Host "✓ Model already exists (skipping training)" -ForegroundColor Green
} else {
    python src\models\train.py
    Write-Host "✓ Model trained successfully" -ForegroundColor Green
}

# Step 6: Run tests
Write-Host ""
Write-Host "[6/6] Running tests..." -ForegroundColor Yellow
pytest tests\ -v --tb=short
Write-Host "✓ Tests completed" -ForegroundColor Green

# Complete
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start API: python src\api\app.py" -ForegroundColor White
Write-Host "  2. Test API: curl http://localhost:8080/health" -ForegroundColor White
Write-Host "  3. View docs: See README.md and docs\QUICK_START.md" -ForegroundColor White
Write-Host ""
Write-Host "To start the API now, run:" -ForegroundColor Yellow
Write-Host "  python src\api\app.py" -ForegroundColor Cyan
Write-Host ""
