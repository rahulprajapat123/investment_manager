# Calculation Issue Analysis and Fix Summary

## Issue Identified

### Problem
When manually analyzing the raw data files and comparing with system-generated reports, the calculations for stock quantities, values, and aggregations were **significantly incorrect**. 

For example:
- **MARUTI stock for C001:**
  - Expected (from raw data): 6,112 Buy qty across 6 brokers
  - System was showing: Only 461 Buy qty (only from Zerodha)
  - Missing data from: Groww, HDFC Bank, ICICI Direct, Fidelity, Charles Schwab

### Root Cause
The ingestion module's `extract_client_broker_from_path()` function expected a specific directory structure:
```
data/
  C001/
    BrokerName/
      file.xlsx
```

But the actual data structure was:
```
data/
  C001/
    tradeBook_BrokerName.xlsx
    capitalGains_BrokerName.xlsx
```

The broker name was embedded in the **filename**, not as a **subfolder**. This caused the ingestion to fail for all files that didn't match the expected structure, resulting in:
- Only files from "Uploaded_Files" folder being processed (if any existed)
- Missing 83% of the data (30 out of 36 files were not being ingested)
- Incorrect aggregations, weighted averages, and portfolio calculations

## Fix Implemented

### Modified File
`src/ingestion.py` - Function: `extract_client_broker_from_path()`

### Changes Made
Updated the function to support BOTH directory structures:
1. **Folder-based broker identification** (original): `data/C001/BrokerName/file.xlsx`
2. **Filename-based broker identification** (new): `data/C001/tradeBook_BrokerName.xlsx`

The function now:
- First tries to find broker from folder structure
- If not found, extracts broker name from filename (after underscore)
- Properly handles both naming conventions simultaneously

### Code Change
```python
def extract_client_broker_from_path(file_path: str) -> Tuple[str, str]:
    """
    Extract client_id and broker from file path.
    
    Expected structures: 
    - .../C001/Charles_Schwab/file.xlsx (broker as subfolder)
    - .../C001/tradeBook_HDFC_Bank.xlsx (broker in filename)
    """
    # ... existing client_id extraction logic ...
    
    # If broker not found in path, extract from filename
    if not broker:
        if '_' in file_name:
            parts = file_name.split('_', 1)
            if len(parts) == 2:
                broker = parts[1].replace('_', ' ')
        
        if not broker:
            broker = "Unknown"
    
    return client_id, broker
```

## Verification Results

After applying the fix and regenerating reports, verified multiple stocks across both trade data and capital gains:

### Trade Data Verification
| Stock | Raw Buy Qty | Report Buy Qty | Raw Sell Qty | Report Sell Qty | Status |
|-------|-------------|----------------|--------------|-----------------|--------|
| MARUTI | 6,112 | 6,112 | 3,269 | 3,269 | ✓ Correct |
| HDFCBANK | 3,885 | 3,885 | 3,006 | 3,006 | ✓ Correct |
| ICICIBANK | 2,273 | 2,273 | 2,431 | 2,431 | ✓ Correct |
| RELIANCE | 4,459 | 4,459 | 6,130 | 6,130 | ✓ Correct |
| TCS | 3,157 | 3,157 | 1,251 | 1,251 | ✓ Correct |
| ITC | 6,067 | 6,067 | 4,362 | 4,362 | ✓ Correct |

### Capital Gains Verification
| Stock | Raw Transactions | Report Transactions | Raw P&L | Report P&L | Status |
|-------|------------------|---------------------|---------|------------|--------|
| HDFCBANK | 16 | 16 | 177,049.45 | 177,049.45 | ✓ Correct |
| RELIANCE | 24 | 24 | 639,501.01 | 639,501.01 | ✓ Correct |
| ITC | 17 | 17 | 629,766.45 | 629,766.45 | ✓ Correct |

**All calculations verified and confirmed correct!**

## Impact

### Before Fix
- Files ingested: 6 out of 36 (only Zerodha for C001)
- Data completeness: ~17%
- Calculations: Incorrect (missing 83% of trades)

### After Fix
- Files ingested: 36 out of 36 (all brokers for all clients)
- Data completeness: 100%
- Calculations: Verified correct across multiple stocks
- Weighted average prices: Correct
- Aggregations: Correct

## Brokers Now Successfully Processed
For C001:
- ✓ Charles Schwab (2 files)
- ✓ Fidelity (2 files)
- ✓ Groww (2 files)
- ✓ HDFC Bank (2 files)
- ✓ ICICI Direct (2 files)
- ✓ Zerodha (2 files)

## Recommendations
1. Keep the fix as it supports both naming conventions
2. Consider standardizing on one approach for future data uploads
3. Add validation to check if expected number of broker files are being processed
4. Consider adding a summary log showing which brokers were processed for each client

## Date Fixed
December 27, 2025
