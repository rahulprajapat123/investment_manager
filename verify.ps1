# Test Script - Verify Installation
# Run this to check if everything is set up correctly

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION VERIFICATION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Test 1: Python
Write-Host "[1/7] Testing Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found" -ForegroundColor Red
    $allGood = $false
}

# Test 2: Virtual Environment
Write-Host "[2/7] Testing virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Virtual environment not found" -ForegroundColor Red
    Write-Host "     Run: python -m venv venv" -ForegroundColor Yellow
    $allGood = $false
}

# Test 3: Dependencies
Write-Host "[3/7] Testing dependencies..." -ForegroundColor Yellow
.\venv\Scripts\activate
try {
    python -c "import pandas, sklearn, flask" 2>$null
    Write-Host "  ✓ Core packages installed" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Some packages missing" -ForegroundColor Red
    Write-Host "     Run: pip install -r requirements.txt" -ForegroundColor Yellow
    $allGood = $false
}

# Test 4: Data Files
Write-Host "[4/7] Testing data files..." -ForegroundColor Yellow
$dataFiles = @(
    "data\daily_prices.csv",
    "data\portfolio_holdings.csv",
    "data\news_sentiment.csv",
    "data\market_data.csv",
    "data\client_profiles.csv"
)

$missingFiles = @()
foreach ($file in $dataFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host "  ✓ All data files present" -ForegroundColor Green
} else {
    Write-Host "  ✗ Missing data files: $($missingFiles.Count)" -ForegroundColor Red
    Write-Host "     Run: python generate_data.py" -ForegroundColor Yellow
    $allGood = $false
}

# Test 5: Model Files
Write-Host "[5/7] Testing ML model..." -ForegroundColor Yellow
if (Test-Path "models_output\stock_direction_classifier_v1.pkl") {
    Write-Host "  ✓ ML model trained" -ForegroundColor Green
} else {
    Write-Host "  ✗ ML model not found" -ForegroundColor Red
    Write-Host "     Run: python src\models\train.py" -ForegroundColor Yellow
    $allGood = $false
}

# Test 6: Configuration
Write-Host "[6/7] Testing configuration..." -ForegroundColor Yellow
if (Test-Path "config.py") {
    Write-Host "  ✓ Configuration file exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ config.py not found" -ForegroundColor Red
    $allGood = $false
}

# Test 7: Import Test
Write-Host "[7/7] Testing module imports..." -ForegroundColor Yellow
try {
    python -c "from src.utils import get_database; from src.models.predict import StockPredictor; print('OK')" 2>$null
    Write-Host "  ✓ All modules import successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Import errors detected" -ForegroundColor Red
    $allGood = $false
}

# Summary
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  ✅ ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "System is ready! You can now:" -ForegroundColor Green
    Write-Host "  1. Start API: .\start_api.ps1" -ForegroundColor White
    Write-Host "  2. Or run: python src\api\app.py" -ForegroundColor White
} else {
    Write-Host "  ⚠️  SOME TESTS FAILED" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Fix issues above, then run this script again" -ForegroundColor Yellow
    Write-Host "Or run automated setup: .\setup.ps1" -ForegroundColor Yellow
}
Write-Host ""
