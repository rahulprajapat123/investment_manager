"""
Enhanced Holdings Computation with Multi-Broker Tracking
"""
from decimal import Decimal
import pandas as pd
from typing import Dict, List
from decimal_utils import (
    sum_decimals, multiply_decimal, divide_decimal, 
    subtract_decimal, round_decimal
)

def compute_current_holdings_by_broker(trades_df: pd.DataFrame, client_id: str) -> pd.DataFrame:
    """
    Compute current holdings split by broker/platform.
    Each stock held on multiple platforms gets separate rows.
    
    Args:
        trades_df: Normalized trades DataFrame
        client_id: Client ID
    
    Returns:
        DataFrame with holdings split by broker
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
        
        # Get currency
        currency = symbol_broker_trades.iloc[0]['currency']
        
        holdings.append({
            'Asset Name': symbol,
            'Asset Class': 'Equity',
            'Platform': broker,
            'Currency': currency,
            'Quantity': round_decimal(net_qty),
            'Average Cost': round_decimal(avg_buy_price),
            'Current Price': round_decimal(last_price),
            'Current Value': round_decimal(current_value),
            'Total Invested': round_decimal(total_invested),
            'Unrealized P/L': round_decimal(unrealized_pnl),
            'P/L %': round_decimal(unrealized_pnl_pct),
            'Allocation %': Decimal("0")
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


def compute_current_holdings_aggregated(trades_df: pd.DataFrame, client_id: str) -> pd.DataFrame:
    """
    Compute current holdings aggregated across all brokers with platform list.
    Shows total position per stock with all brokers listed.
    
    Args:
        trades_df: Normalized trades DataFrame
        client_id: Client ID
    
    Returns:
        DataFrame with aggregated holdings and platform info
    """
    client_trades = trades_df[trades_df['client_id'] == client_id].copy()
    
    if client_trades.empty:
        return pd.DataFrame()
    
    holdings = []
    
    for symbol in client_trades['symbol'].unique():
        symbol_trades = client_trades[client_trades['symbol'] == symbol].sort_values('date')
        
        # Get all brokers for this symbol
        all_brokers = sorted(symbol_trades['broker'].unique().tolist())
        
        # Calculate net position across all brokers
        buy_trades = symbol_trades[symbol_trades['action'] == 'Buy']
        sell_trades = symbol_trades[symbol_trades['action'] == 'Sell']
        
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
        last_price = symbol_trades.iloc[-1]['price']
        current_value = multiply_decimal(net_qty, last_price)
        
        # Total invested
        total_invested = multiply_decimal(net_qty, avg_buy_price)
        
        # Unrealized P/L
        unrealized_pnl = subtract_decimal(current_value, total_invested)
        unrealized_pnl_pct = divide_decimal(unrealized_pnl, total_invested) * 100 if total_invested != 0 else Decimal("0")
        
        # Primary platform (most recent or largest)
        primary_platform = all_brokers[0]
        platform_display = ', '.join(all_brokers) if len(all_brokers) > 1 else primary_platform
        
        currency = symbol_trades.iloc[0]['currency']
        
        holdings.append({
            'Asset Name': symbol,
            'Asset Class': 'Equity',
            'Platform': primary_platform,
            'All Platforms': platform_display,
            'Currency': currency,
            'Quantity': round_decimal(net_qty),
            'Average Cost': round_decimal(avg_buy_price),
            'Current Price': round_decimal(last_price),
            'Current Value': round_decimal(current_value),
            'Total Invested': round_decimal(total_invested),
            'Unrealized P/L': round_decimal(unrealized_pnl),
            'P/L %': round_decimal(unrealized_pnl_pct),
            'Allocation %': Decimal("0")
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
