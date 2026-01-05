# Multi-Platform Upload Fix

## Problem Identified
The system was only processing files from one platform when multiple platform files were uploaded to the same client because:
1. All uploaded files were stored in a single `Uploaded_Files` folder
2. The broker/platform information was not being captured during upload
3. Files from different platforms couldn't be distinguished

## Solution Implemented

### Frontend Changes (Upload.jsx)
✅ **Added Broker/Platform Selection Field**
- Users must now select the broker/platform when uploading files
- Dropdown includes common brokers: Zerodha, Groww, HDFC Bank, ICICI Direct, Charles Schwab, Fidelity, etc.
- Each upload is associated with a specific broker

### Backend Changes (flask_backend.py)
✅ **Separate Folders Per Broker**
- Files are now stored in: `data/C00X/BrokerName/` instead of `data/C00X/Uploaded_Files/`
- Each broker gets its own folder
- The broker parameter is now required in the upload API

### Data Structure
**Before:**
```
data/
  C003/
    Uploaded_Files/
      tradeBook_platform1.xlsx  ← All mixed together
      tradeBook_platform2.xlsx
      tradeBook_platform3.xlsx
```

**After:**
```
data/
  C003/
    Zerodha/
      tradeBook.xlsx
      capitalGains.xlsx
    Groww/
      tradeBook.xlsx
      capitalGains.xlsx
    HDFC_Bank/
      tradeBook.xlsx
      capitalGains.xlsx
```

## How to Use (Step-by-Step)

### Uploading Files from Multiple Platforms

1. **Go to Upload Page**
2. **For Platform 1 (e.g., Zerodha):**
   - Enter Client ID: `C003`
   - Select Broker: `Zerodha`
   - Upload Zerodha files (tradebook, capital gains)
   - Click "Upload Files"
   - Wait for success message

3. **For Platform 2 (e.g., Groww):**
   - Enter Client ID: `C003` (same client)
   - Select Broker: `Groww`
   - Upload Groww files
   - Click "Upload Files"
   - Wait for success message

4. **For Platform 3 (e.g., HDFC Bank):**
   - Enter Client ID: `C003` (same client)
   - Select Broker: `HDFC_Bank`
   - Upload HDFC files
   - Click "Upload Files"
   - Wait for success message

5. **Generate Report:**
   - Go to Dashboard
   - Select Client C003
   - Click "Generate Report"
   - All 3 platforms will be processed correctly

## Platform Count Calculation

The system now correctly identifies platforms by:
1. Reading broker information from the folder structure
2. Grouping trades by broker
3. Counting unique brokers that have trades
4. Displaying accurate platform count in reports

## Verification

To verify the fix is working:

```python
# Run this to check the data structure
import os
from pathlib import Path

data_dir = Path("data/C003")
for broker_folder in data_dir.iterdir():
    if broker_folder.is_dir():
        files = list(broker_folder.glob("*"))
        print(f"Broker: {broker_folder.name}")
        print(f"  Files: {[f.name for f in files]}")
```

Expected output:
```
Broker: Zerodha
  Files: ['tradeBook.xlsx', 'capitalGains.xlsx']
Broker: Groww
  Files: ['tradeBook.xlsx', 'capitalGains.xlsx']
Broker: HDFC_Bank
  Files: ['tradeBook.xlsx', 'capitalGains.xlsx']
```

## Additional Improvements

### Broker Detection from Filenames (Fallback)
If broker is not explicitly selected, the system can still detect it from:
- Folder names (e.g., `Zerodha`, `Groww`)
- Filename patterns (e.g., `tradeBook_Zerodha.xlsx`)
- Account numbers (e.g., `6500072347_tradeBook.xlsx` → `Account_650007`)

### Report Accuracy
- ✅ Platform count is now accurate
- ✅ All numeric calculations verified (total investment, realized gains, unrealized gains, etc.)
- ✅ Multiple brokers per client fully supported
- ✅ CSV and Excel files both supported

## Migration for Existing Data

If you have existing data in `Uploaded_Files` folders:

1. Create broker-specific folders manually:
   ```
   data/C00X/Zerodha/
   data/C00X/Groww/
   data/C00X/HDFC_Bank/
   ```

2. Move files to appropriate broker folders based on their origin

3. Delete the old `Uploaded_Files` folder

4. Regenerate reports

## Testing

The fix has been tested with:
- ✅ Single platform upload
- ✅ Multiple platforms for the same client
- ✅ Different file types (Excel, CSV)
- ✅ Platform count calculation
- ✅ Report generation with multiple brokers

## Known Limitations

1. Each upload session can only handle files from ONE broker
2. To upload from multiple brokers, you must make separate upload submissions
3. This is by design to ensure accurate broker tracking

## Support

If you encounter issues:
1. Check that you selected the correct broker
2. Verify folder structure in `data/C00X/`
3. Check backend logs for errors
4. Ensure all files are valid Excel/CSV formats
