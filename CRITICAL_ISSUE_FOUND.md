# CRITICAL ISSUE DISCOVERED: DATA CORRUPTION IN REPORT GENERATION

## Problem Identified

The **Calculations sheet** in the generated reports has **DATA CORRUPTION**. The capital gains data has been mixed into the trades data, causing:

1. **Action column contains dates** instead of just 'Buy'/'Sell'
   - Found 219 different values including dates like "2024-11-22 00:00:00"
   - Should only contain 'Buy' and 'Sell'

2. **Negative net positions** for stocks
   - Example: TSLA has net position of -830 (sold more than bought)
   - This is mathematically impossible unless data is corrupted

3. **Empty Holdings** despite having trades
   - All stocks show net quantity = 0 when using incorrect case
   - When using correct case, many stocks show negative positions

## Root Cause

The report_generator.py is mixing capital gains records with trade records in the Calculations sheet. The capital gains data has columns like 'sale_date' which is being written to the 'action' column.

## Impact

- **Holdings calculations are INCORRECT** 
- Stocks that should appear in holdings don't show up
- The 10 stocks that DO appear in holdings are coming from OTHER data (likely holdings.csv files)
- The trade aggregation is NOT working properly

## What This Means

The verification I did earlier was MISLEADING. The system is NOT correctly:
1. Aggregating trades across brokers
2. Calculating net positions from trades  
3. Determining which stocks should be in current holdings

The 10 holdings showing in the report (NVDA, JPM, META, etc.) are likely coming from the holdings.csv files directly, NOT from trade aggregation.

## Fix Required

The report_generator.py needs to:
1. Keep trades and capital gains separate
2. NOT mix dates/sale_dates into the action column
3. Properly aggregate trades to calculate net positions
4. Generate holdings based on correct net position calculations

---

**STATUS: The data processing pipeline has CRITICAL BUGS that need to be fixed before reports can be trusted.**
