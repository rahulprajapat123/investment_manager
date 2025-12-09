# Start the Investment Platform API Server
# Run this script to start the Flask API

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  INVESTMENT PLATFORM API" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\activate

# Start API
Write-Host ""
Write-Host "Starting API server..." -ForegroundColor Yellow
Write-Host "API will be available at: http://localhost:8080" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python src\api\app.py
