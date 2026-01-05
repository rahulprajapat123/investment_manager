"""
Report generation module for creating Excel reports.
Generates multi-sheet reports per client matching test1_portfolio format.
"""
import pandas as pd
from decimal import Decimal
from pathlib import Path
from typing import Dict
import xlsxwriter
from datetime import datetime
from decimal_utils import (
    to_decimal, round_decimal, divide_decimal, 
    sum_decimals, multiply_decimal, subtract_decimal
)


def format_decimal_for_excel(value):
    """Convert Decimal to float for Excel."""
    if isinstance(value, Decimal):
        return float(value)
    return value


def prepare_df_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for Excel export by converting Decimals to floats.
    
    Args:
        df: DataFrame
    
    Returns:
        DataFrame with converted values
    """
    if df.empty:
        return df
    
    df_copy = df.copy()
    
    for col in df_copy.columns:
        if df_copy[col].dtype == 'object':
            # Check if column contains Decimals
            if len(df_copy) > 0 and isinstance(df_copy[col].iloc[0], Decimal):
                df_copy[col] = df_copy[col].apply(format_decimal_for_excel)
    
    return df_copy


def compute_current_holdings(trades_df: pd.DataFrame, client_id: str) -> pd.DataFrame:
    """
    Compute current holdings from trades (buy - sell).
    
    Args:
        trades_df: Normalized trades DataFrame
        client_id: Client ID
    
    Returns:
        DataFrame with current holdings
    """
    client_trades = trades_df[trades_df['client_id'] == client_id].copy()
    
    if client_trades.empty:
        return pd.DataFrame()
    
    holdings = []
    
    for symbol in client_trades['symbol'].unique():
        symbol_trades = client_trades[client_trades['symbol'] == symbol].sort_values('date')
        
        # Calculate net position
        buy_trades = symbol_trades[symbol_trades['action'] == 'Buy']
        sell_trades = symbol_trades[symbol_trades['action'] == 'Sell']
        
        total_buy_qty = sum_decimals(*buy_trades['qty'].tolist()) if not buy_trades.empty else Decimal("0")
        total_sell_qty = sum_decimals(*sell_trades['qty'].tolist()) if not sell_trades.empty else Decimal("0")
        
        net_qty = subtract_decimal(total_buy_qty, total_sell_qty)
        
        # Skip if position is closed or negative (data quality issue)
        if net_qty <= 0:
            continue
        
        # Calculate weighted average buy price
        total_buy_value = sum_decimals(*[multiply_decimal(row['qty'], row['price']) 
                                         for _, row in buy_trades.iterrows()]) if not buy_trades.empty else Decimal("0")
        
        avg_buy_price = divide_decimal(total_buy_value, total_buy_qty) if total_buy_qty > 0 else Decimal("0")
        
        # Current value = net_qty * avg_buy_price (since we don't have real-time prices)
        # Using last traded price as proxy for current price
        last_price = symbol_trades.iloc[-1]['price']
        current_value = multiply_decimal(net_qty, last_price)
        
        # Total invested (cost basis) = net_qty * avg_buy_price
        total_invested = multiply_decimal(net_qty, avg_buy_price)
        
        # Unrealized P/L
        unrealized_pnl = subtract_decimal(current_value, total_invested)
        unrealized_pnl_pct = divide_decimal(unrealized_pnl, total_invested) * 100 if total_invested != 0 else Decimal("0")
        
        # Get platform and currency (from first trade)
        first_trade = symbol_trades.iloc[0]
        currency = first_trade['currency']
        
        # Get all unique brokers for this symbol (for better tracking)
        all_brokers = symbol_trades['broker'].unique().tolist() if 'broker' in symbol_trades.columns else [first_trade['broker']]
        platform = all_brokers[0]  # Use first broker as primary
        # Store all brokers in metadata (if multiple)
        platform_note = ', '.join(all_brokers) if len(all_brokers) > 1 else platform
        
        holdings.append({
            'Asset Name': symbol,
            'Asset Class': 'Equity',  # Default to Equity for stocks
            'Platform': platform,
            'Currency': currency,
            'Quantity': round_decimal(net_qty),
            'Average Cost': round_decimal(avg_buy_price),
            'Current Price': round_decimal(last_price),
            'Current Value': round_decimal(current_value),
            'Total Invested': round_decimal(total_invested),
            'Unrealized P/L': round_decimal(unrealized_pnl),
            'P/L %': round_decimal(unrealized_pnl_pct),
            'Allocation %': Decimal("0")  # Will calculate after we have total
        })
    
    if not holdings:
        return pd.DataFrame()
    
    holdings_df = pd.DataFrame(holdings)
    
    # Calculate allocations
    total_value = sum_decimals(*holdings_df['Current Value'].tolist())
    if total_value != 0:
        holdings_df['Allocation %'] = holdings_df['Current Value'].apply(
            lambda x: round_decimal(divide_decimal(x, total_value) * 100, places=4)
        )
    
    return holdings_df


def generate_summary_sheet(writer, workbook, client_id: str, trades_df: pd.DataFrame, 
                           cg_df: pd.DataFrame, holdings_df: pd.DataFrame):
    """Generate Summary sheet with key metrics."""
    
    # Calculate metrics
    if not holdings_df.empty:
        total_current_value = sum_decimals(*holdings_df['Current Value'].tolist())
        total_invested = sum_decimals(*holdings_df['Total Invested'].tolist())
        unrealized_pnl = sum_decimals(*holdings_df['Unrealized P/L'].tolist())
        unrealized_pnl_pct = divide_decimal(unrealized_pnl, total_invested) * 100 if total_invested != 0 else Decimal("0")
        num_holdings = len(holdings_df)
    else:
        total_current_value = Decimal("0")
        total_invested = Decimal("0")
        unrealized_pnl = Decimal("0")
        unrealized_pnl_pct = Decimal("0")
        num_holdings = 0
    
    # Realized P/L
    if not cg_df.empty:
        realized_pnl = sum_decimals(*cg_df['pnl'].tolist())
    else:
        realized_pnl = Decimal("0")
    
    # Net total return
    net_total_return = sum_decimals(realized_pnl, unrealized_pnl)
    net_return_pct = divide_decimal(net_total_return, total_invested) * 100 if total_invested != 0 else Decimal("0")
    
    # Number of platforms - Count unique brokers from TRADES data (more accurate)
    # This captures all platforms used, not just those with current holdings
    client_trades = trades_df[trades_df['client_id'] == client_id] if not trades_df.empty else pd.DataFrame()
    num_platforms = client_trades['broker'].nunique() if not client_trades.empty and 'broker' in client_trades.columns else 0
    
    # Asset classes
    num_asset_classes = holdings_df['Asset Class'].nunique() if not holdings_df.empty else 0
    
    # Base currency (most common)
    base_currency = holdings_df['Currency'].mode()[0] if not holdings_df.empty else 'USD'
    
    # Create broker/platform breakdown
    platform_breakdown = []
    if not client_trades.empty and 'broker' in client_trades.columns:
        broker_stats = client_trades.groupby('broker').agg({
            'symbol': 'nunique',  # unique stocks
            'qty': 'count'  # number of trades
        }).reset_index()
        broker_stats.columns = ['Broker', 'Unique Stocks', 'Number of Trades']
        platform_breakdown = broker_stats.to_dict('records')
    
    # Create summary data
    summary_data = [
        ['Portfolio Analytics Report', ''],
        [f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ''],
        ['', ''],
        ['Key Metrics', ''],
        ['Total Current Value', format_decimal_for_excel(total_current_value)],
        ['Total Invested', format_decimal_for_excel(total_invested)],
        ['Unrealized P/L', format_decimal_for_excel(unrealized_pnl)],
        ['Unrealized P/L %', format_decimal_for_excel(unrealized_pnl_pct / 100)],
        ['Realized P/L', format_decimal_for_excel(realized_pnl)],
        ['Net Total Return', format_decimal_for_excel(net_total_return)],
        ['Net Return %', format_decimal_for_excel(net_return_pct / 100)],
        ['', ''],
        ['Dividends Earned', 0.00],
        ['Interest Earned', 0.00],
        ['Fees Paid', 0.00],
        ['Taxes Paid', 0.00],
        ['', ''],
        ['Number of Holdings', num_holdings],
        ['Number of Platforms', num_platforms],
        ['Asset Classes', num_asset_classes],
        ['Base Currency', base_currency],
        ['Cost Basis Method', 'FIFO'],
        ['', ''],
        ['Platform Breakdown', ''],
    ]
    
    # Add broker breakdown details
    if platform_breakdown:
        for broker_info in platform_breakdown:
            summary_data.append([
                f"  - {broker_info['Broker']}", 
                f"{broker_info['Unique Stocks']} stocks, {broker_info['Number of Trades']} trades"
            ])
    else:
        summary_data.append(['  No platform data', ''])
    
    summary_df = pd.DataFrame(summary_data, columns=['Portfolio Analytics Report', 'Unnamed: 1'])
    summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
    
    # Format the sheet
    worksheet = writer.sheets['Summary']
    
    # Format title row (bold)
    title_format = workbook.add_format({'bold': True, 'font_size': 14})
    worksheet.write(0, 0, 'Portfolio Analytics Report', title_format)
    
    # Format section headers
    section_format = workbook.add_format({'bold': True, 'font_size': 11})
    worksheet.write(3, 0, 'Key Metrics', section_format)
    
    # Format money values
    money_format = workbook.add_format({'num_format': '$#,##0.00'})
    for row in [4, 5, 6, 8, 9, 12, 13, 14, 15]:
        worksheet.write(row, 1, summary_df.iloc[row, 1], money_format)
    
    # Format percentages
    percent_format = workbook.add_format({'num_format': '0.00%'})
    for row in [7, 10]:
        worksheet.write(row, 1, summary_df.iloc[row, 1], percent_format)
    
    # Set column widths
    worksheet.set_column(0, 0, 30)
    worksheet.set_column(1, 1, 20)


def generate_allocations_sheet(writer, workbook, holdings_df: pd.DataFrame):
    """Generate Allocations sheet."""
    
    if holdings_df.empty:
        # Create empty allocations sheet
        pd.DataFrame().to_excel(writer, sheet_name='Allocations', index=False)
        return
    
    total_value = sum_decimals(*holdings_df['Current Value'].tolist())
    
    # Allocation by Asset Class
    asset_class_alloc = holdings_df.groupby('Asset Class').agg({
        'Current Value': lambda x: sum_decimals(*x.tolist())
    }).reset_index()
    asset_class_alloc.columns = ['Asset Class', 'Value']
    asset_class_alloc['Allocation %'] = asset_class_alloc['Value'].apply(
        lambda x: divide_decimal(x, total_value) if total_value != 0 else Decimal("0")
    )
    
    # Allocation by Platform
    platform_alloc = holdings_df.groupby('Platform').agg({
        'Current Value': lambda x: sum_decimals(*x.tolist())
    }).reset_index()
    platform_alloc.columns = ['Platform', 'Value']
    platform_alloc['Allocation %'] = platform_alloc['Value'].apply(
        lambda x: divide_decimal(x, total_value) if total_value != 0 else Decimal("0")
    )
    
    # Allocation by Currency
    currency_alloc = holdings_df.groupby('Currency').agg({
        'Current Value': lambda x: sum_decimals(*x.tolist())
    }).reset_index()
    currency_alloc.columns = ['Currency', 'Value']
    currency_alloc['Allocation %'] = currency_alloc['Value'].apply(
        lambda x: divide_decimal(x, total_value) if total_value != 0 else Decimal("0")
    )
    
    # Combine into single view
    alloc_data = []
    
    # Asset Class section
    alloc_data.append(['Allocation by Asset Class', '', ''])
    alloc_data.append(['Asset Class', 'Allocation %', 'Value'])
    for _, row in asset_class_alloc.iterrows():
        alloc_data.append([row['Asset Class'], format_decimal_for_excel(row['Allocation %']), 
                          format_decimal_for_excel(row['Value'])])
    alloc_data.append(['', '', ''])
    alloc_data.append(['', '', ''])
    
    # Platform section
    alloc_data.append(['Allocation by Platform', '', ''])
    alloc_data.append(['Platform', 'Allocation %', 'Value'])
    for _, row in platform_alloc.iterrows():
        alloc_data.append([row['Platform'], format_decimal_for_excel(row['Allocation %']), 
                          format_decimal_for_excel(row['Value'])])
    alloc_data.append(['', '', ''])
    alloc_data.append(['', '', ''])
    
    # Currency section
    alloc_data.append(['Allocation by Currency', '', ''])
    alloc_data.append(['Currency', 'Allocation %', 'Value'])
    for _, row in currency_alloc.iterrows():
        alloc_data.append([row['Currency'], format_decimal_for_excel(row['Allocation %']), 
                          format_decimal_for_excel(row['Value'])])
    
    alloc_df = pd.DataFrame(alloc_data, columns=['Allocation by Asset Class', 'Unnamed: 1', 'Unnamed: 2'])
    alloc_df.to_excel(writer, sheet_name='Allocations', index=False, header=False)
    
    worksheet = writer.sheets['Allocations']
    
    # Format section headers
    section_format = workbook.add_format({'bold': True, 'font_size': 11})
    worksheet.write(0, 0, 'Allocation by Asset Class', section_format)
    worksheet.write(len(asset_class_alloc) + 4, 0, 'Allocation by Platform', section_format)
    worksheet.write(len(asset_class_alloc) + len(platform_alloc) + 8, 0, 'Allocation by Currency', section_format)
    
    worksheet.set_column(0, 0, 25)
    worksheet.set_column(1, 1, 15)
    worksheet.set_column(2, 2, 15)


def generate_calculations_sheet(writer, workbook, trades_df: pd.DataFrame, 
                                cg_df: pd.DataFrame, header_format, money_format):
    """Generate Calculations sheet with raw data."""
    
    # Prepare data
    trades_excel = prepare_df_for_excel(trades_df)
    cg_excel = prepare_df_for_excel(cg_df)
    
    # Write trades
    if not trades_excel.empty:
        trades_excel.to_excel(writer, sheet_name='Calculations', index=False, startrow=0)
        worksheet = writer.sheets['Calculations']
        
        # Format header
        for col_num, value in enumerate(trades_excel.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Add capital gains below trades (with spacing)
        if not cg_excel.empty:
            start_row = len(trades_excel) + 3
            cg_excel.to_excel(writer, sheet_name='Calculations', index=False, startrow=start_row)
            
            # Format CG header
            for col_num, value in enumerate(cg_excel.columns.values):
                worksheet.write(start_row, col_num, value, header_format)
    elif not cg_excel.empty:
        cg_excel.to_excel(writer, sheet_name='Calculations', index=False)
        worksheet = writer.sheets['Calculations']
        
        # Format header
        for col_num, value in enumerate(cg_excel.columns.values):
            worksheet.write(0, col_num, value, header_format)


def compute_holdings_by_broker(trades_df: pd.DataFrame, client_id: str) -> pd.DataFrame:
    """
    Compute holdings split by broker - each stock on each platform gets its own row.
    """
    client_trades = trades_df[trades_df['client_id'] == client_id].copy()
    
    if client_trades.empty:
        return pd.DataFrame()
    
    holdings = []
    
    # Group by symbol AND broker
    for (symbol, broker), group in client_trades.groupby(['symbol', 'broker']):
        symbol_broker_trades = group.sort_values('date')
        
        # Calculate net position for this symbol on this broker
        buy_trades = symbol_broker_trades[symbol_broker_trades['action'] == 'Buy']
        sell_trades = symbol_broker_trades[symbol_broker_trades['action'] == 'Sell']
        
        total_buy_qty = sum_decimals(*buy_trades['qty'].tolist()) if not buy_trades.empty else Decimal("0")
        total_sell_qty = sum_decimals(*sell_trades['qty'].tolist()) if not sell_trades.empty else Decimal("0")
        
        net_qty = subtract_decimal(total_buy_qty, total_sell_qty)
        
        # Skip if position is closed or negative
        if net_qty <= 0:
            continue
        
        # Calculate weighted average buy price
        total_buy_value = sum_decimals(*[multiply_decimal(row['qty'], row['price']) 
                                         for _, row in buy_trades.iterrows()]) if not buy_trades.empty else Decimal("0")
        
        avg_buy_price = divide_decimal(total_buy_value, total_buy_qty) if total_buy_qty > 0 else Decimal("0")
        
        # Current value
        last_price = symbol_broker_trades.iloc[-1]['price']
        current_value = multiply_decimal(net_qty, last_price)
        
        # Total invested
        total_invested = multiply_decimal(net_qty, avg_buy_price)
        
        # Unrealized P/L
        unrealized_pnl = subtract_decimal(current_value, total_invested)
        unrealized_pnl_pct = divide_decimal(unrealized_pnl, total_invested) * 100 if total_invested != 0 else Decimal("0")
        
        currency = symbol_broker_trades.iloc[0]['currency']
        
        holdings.append({
            'Asset Name': symbol,
            'Broker': broker,
            'Asset Class': 'Equity',
            'Currency': currency,
            'Quantity': round_decimal(net_qty),
            'Average Cost': round_decimal(avg_buy_price),
            'Current Price': round_decimal(last_price),
            'Current Value': round_decimal(current_value),
            'Total Invested': round_decimal(total_invested),
            'Unrealized P/L': round_decimal(unrealized_pnl),
            'P/L %': round_decimal(unrealized_pnl_pct),
        })
    
    if not holdings:
        return pd.DataFrame()
    
    return pd.DataFrame(holdings)


def generate_client_report(client_id: str,
                           trades_df: pd.DataFrame,
                           cg_df: pd.DataFrame,
                           aggregated_metrics: Dict[str, pd.DataFrame],
                           validation_results: Dict,
                           output_dir: str):
    """
    Generate Excel report for a client matching test1_portfolio format.
    
    Args:
        client_id: Client ID
        trades_df: Normalized trades DataFrame (for this client)
        cg_df: Normalized capital gains DataFrame (for this client)
        aggregated_metrics: Dictionary with aggregated DataFrames
        validation_results: Validation results dictionary
        output_dir: Output directory for reports
    """
    output_path = Path(output_dir) / f"{client_id}_portfolio_report.xlsx"
    
    # Compute holdings (aggregated view)
    holdings_df = compute_current_holdings(trades_df, client_id)
    
    # Compute holdings by broker (detailed view)
    holdings_by_broker_df = compute_holdings_by_broker(trades_df, client_id)
    
    # Create Excel writer with xlsxwriter engine
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        money_format = workbook.add_format({
            'num_format': '#,##0.00'
        })
        
        percent_format = workbook.add_format({
            'num_format': '0.00%'
        })
        
        # Sheet 1: Summary
        generate_summary_sheet(writer, workbook, client_id, trades_df, cg_df, holdings_df)
        
        # Sheet 2: Holdings
        if not holdings_df.empty:
            holdings_excel = prepare_df_for_excel(holdings_df)
            holdings_excel.to_excel(writer, sheet_name='Holdings', index=False)
            worksheet = writer.sheets['Holdings']
            
            # Format header
            for col_num, value in enumerate(holdings_excel.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Format money columns
            money_cols = ['Average Cost', 'Current Price', 'Current Value', 'Total Invested', 'Unrealized P/L']
            for col in money_cols:
                if col in holdings_excel.columns:
                    col_idx = holdings_excel.columns.get_loc(col)
                    for row_num in range(1, len(holdings_excel) + 1):
                        worksheet.write(row_num, col_idx, 
                                      holdings_excel.iloc[row_num-1][col],
                                      money_format)
            
            # Format percent columns
            percent_cols = ['P/L %', 'Allocation %']
            for col in percent_cols:
                if col in holdings_excel.columns:
                    col_idx = holdings_excel.columns.get_loc(col)
                    for row_num in range(1, len(holdings_excel) + 1):
                        val = holdings_excel.iloc[row_num-1][col] / 100  # Convert to decimal
                        worksheet.write(row_num, col_idx, val, percent_format)
            
            # Auto-adjust column widths
            for idx, col in enumerate(holdings_excel.columns):
                max_len = min(30, max(
                    holdings_excel[col].astype(str).map(len).max(),
                    len(str(col))
                ))
                worksheet.set_column(idx, idx, max_len + 2)
        
        # Sheet 3: Holdings by Broker (detailed multi-broker view)
        if not holdings_by_broker_df.empty:
            holdings_broker_excel = prepare_df_for_excel(holdings_by_broker_df)
            holdings_broker_excel.to_excel(writer, sheet_name='Holdings by Broker', index=False)
            worksheet = writer.sheets['Holdings by Broker']
            
            # Format header
            for col_num, value in enumerate(holdings_broker_excel.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Format money columns
            money_cols = ['Average Cost', 'Current Price', 'Current Value', 'Total Invested', 'Unrealized P/L']
            for col in money_cols:
                if col in holdings_broker_excel.columns:
                    col_idx = holdings_broker_excel.columns.get_loc(col)
                    for row_num in range(1, len(holdings_broker_excel) + 1):
                        worksheet.write(row_num, col_idx, 
                                      holdings_broker_excel.iloc[row_num-1][col],
                                      money_format)
            
            # Format percent columns
            percent_cols = ['P/L %']
            for col in percent_cols:
                if col in holdings_broker_excel.columns:
                    col_idx = holdings_broker_excel.columns.get_loc(col)
                    for row_num in range(1, len(holdings_broker_excel) + 1):
                        val = holdings_broker_excel.iloc[row_num-1][col] / 100
                        worksheet.write(row_num, col_idx, val, percent_format)
            
            # Auto-adjust column widths
            for idx, col in enumerate(holdings_broker_excel.columns):
                max_len = min(30, max(
                    holdings_broker_excel[col].astype(str).map(len).max(),
                    len(str(col))
                ))
                worksheet.set_column(idx, idx, max_len + 2)
        
        # Sheet 4: Allocations
        generate_allocations_sheet(writer, workbook, holdings_df)
        
        # Sheet 5: Calculations (detailed raw data)
        generate_calculations_sheet(writer, workbook, trades_df, cg_df, header_format, money_format)
    
    print(f"Generated report: {output_path}")


def generate_all_reports(trades_df: pd.DataFrame,
                        cg_df: pd.DataFrame,
                        validation_results: Dict,
                        output_dir: str):
    """
    Generate reports for all clients.
    
    Args:
        trades_df: All normalized trades
        cg_df: All normalized capital gains
        validation_results: Validation results
        output_dir: Output directory
    """
    # Get all clients
    clients = set()
    if not trades_df.empty:
        clients.update(trades_df['client_id'].unique())
    if not cg_df.empty:
        clients.update(cg_df['client_id'].unique())
    
    clients = sorted(list(clients))
    
    if not clients:
        print("No clients found in data")
        return
    
    print(f"Generating reports for {len(clients)} clients...")
    
    for client_id in clients:
        # Filter data for client
        client_trades = trades_df[trades_df['client_id'] == client_id]
        client_cg = cg_df[cg_df['client_id'] == client_id]
        
        # Generate report
        generate_client_report(
            client_id,
            client_trades,
            client_cg,
            {},  # aggregated_metrics not needed in new format
            validation_results,
            output_dir
        )
    
    print(f"All reports generated in: {output_dir}")
