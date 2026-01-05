# Multi-Platform Upload Guide

## What Changed?

The system now supports **simultaneous upload from multiple brokers/platforms** with automatic aggregation.

## How It Works

### 1. Upload Process

#### Step 1: Enter Client ID
```
Client ID: C003 (or just 3)
```

#### Step 2: Select All Files at Once
- Click or drag **multiple files from different platforms**
- Example:
  - zerodha_tradebook.xlsx
  - groww_trades.xlsx  
  - hdfc_capital_gains.xlsx
  - icici_holdings.csv

#### Step 3: Assign Brokers (Auto-Detected)
The system automatically detects brokers from filenames:
- Files with "zerodha" → Zerodha
- Files with "groww" → Groww
- Files with "hdfc" → HDFC_Bank
- Files with "icici" → ICICI_Direct
- Files with "schwab" → Charles_Schwab
- Files with "fidelity" → Fidelity
- Files with "angel" → Angel_One
- Files with "upstox" → Upstox

If not detected, you can manually assign from the dropdown.

#### Step 4: Upload All Together
Click **"Upload X files from Y platforms"**

### 2. What Happens Behind the Scenes

```
Client C003/
├── Zerodha/
│   └── zerodha_tradebook.xlsx
├── Groww/
│   └── groww_trades.xlsx
├── HDFC_Bank/
│   └── hdfc_capital_gains.xlsx
└── ICICI_Direct/
    └── icici_holdings.csv
```

### 3. Processing & Reports

When you click **"Generate Report"** on the dashboard:

1. **All platforms processed together**
2. **Trades aggregated across brokers**
3. **Single comprehensive report** showing:
   - Total holdings from all platforms
   - Platform breakdown
   - Aggregated P&L
   - Number of platforms: 4 (correct count!)

## Key Improvements

### Before ❌
- Upload one platform at a time
- Broker hardcoded as "Uploaded_Files"
- Platform count always showed 1
- Manual folder organization needed

### After ✅
- Upload all platforms simultaneously
- Auto-detect broker from filename
- Accurate platform counting
- Automatic organization by broker
- **Aggregated reports across all platforms**

## Example Usage

### Scenario: Client has 3 brokers

**Files to upload:**
1. `account_zerodha_trades.xlsx`
2. `account_zerodha_holdings.csv`
3. `groww_statement.xlsx`
4. `hdfc_portfolio.xlsx`

**Process:**
1. Select all 4 files at once
2. System auto-detects:
   - Files 1-2 → Zerodha
   - File 3 → Groww
   - File 4 → HDFC_Bank
3. Click "Upload 4 files from 3 platforms"
4. All files uploaded and organized
5. Generate report → Shows aggregated data from all 3 brokers

## Platform Calculation Fix

### Original Issue
```python
# OLD: Only counted platforms in current holdings
num_platforms = holdings_df['Platform'].nunique()  
# Problem: Only shows first broker per stock
```

### Fixed Implementation
```python
# NEW: Counts all brokers from trades data
client_trades = trades_df[trades_df['client_id'] == client_id]
num_platforms = client_trades['broker'].nunique()
# Result: Accurate count of all platforms used
```

## Backend Changes

### Upload Endpoint
- Now accepts multiple file uploads per broker
- Creates separate folder for each broker
- Groups files by broker automatically

### Broker Detection
- Improved extraction from filenames
- Ignores generic folder names ("Uploaded_Files")
- Falls back to account numbers if broker unknown

### Report Generation
- Platform count from trades (not holdings)
- Shows broker breakdown in summary
- Tracks all brokers per stock symbol

## Testing

Run the verification script:
```bash
python verify_numeric_calculations.py C003
```

This will show:
- ✓ Broker extraction accuracy
- ✓ Platform count correctness  
- ✓ Numeric calculation precision
- ✓ Data quality score

## Benefits

1. **User-Friendly**: One-time upload for all platforms
2. **Accurate**: Correct platform counting
3. **Organized**: Automatic folder structure
4. **Comprehensive**: Aggregated reports across all brokers
5. **Flexible**: Manual override for broker assignment
6. **Smart**: Auto-detection from filenames

## Notes

- Supported formats: .xlsx, .xls, .csv
- No file size limits (within browser limits)
- Upload happens per broker (but feels simultaneous)
- Each broker gets its own folder
- Reports aggregate across all brokers automatically
