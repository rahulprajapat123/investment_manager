"""
Aggregation module for computing portfolio metrics.
Includes weighted average buy prices, realized P&L, and performance analysis.
"""
import pandas as pd
from decimal import Decimal
from typing import Dict, List, Tuple
from decimal_utils import (
    to_decimal, round_decimal, divide_decimal, 
    sum_decimals, multiply_decimal
)


def compute_weighted_avg_buy_price(trades_df: pd.DataFrame, 
                                   client_id: str = None,
                                   symbol: str = None) -> pd.DataFrame:
    """
    Compute weighted average buy price per stock per client.
    
    Formula: Total Buy Value / Total Buy Quantity
    
    Args:
        trades_df: Normalized trades DataFrame
        client_id: Optional client filter
        symbol: Optional symbol filter
    
    Returns:
        DataFrame with columns: client_id, symbol, total_buy_qty, 
                                total_buy_value, weighted_avg_buy_price
    """
    if trades_df.empty:
        return pd.DataFrame()
    
    # Filter if needed
    df = trades_df.copy()
    if client_id:
        df = df[df['client_id'] == client_id]
    if symbol:
        df = df[df['symbol'] == symbol]
    
    # Filter for Buy actions only
    buy_df = df[df['action'] == 'Buy'].copy()
    
    if buy_df.empty:
        return pd.DataFrame()
    
    # Group by client and symbol
    grouped = buy_df.groupby(['client_id', 'symbol'])
    
    results = []
    
    for (cid, sym), group in grouped:
        # Calculate total buy quantity
        total_qty = sum_decimals(*group['qty'].tolist())
        
        # Calculate total buy value (qty * price for each trade)
        buy_values = []
        for _, row in group.iterrows():
            value = multiply_decimal(row['qty'], row['price'])
            buy_values.append(value)
        
        total_value = sum_decimals(*buy_values)
        
        # Calculate weighted average
        if total_qty > 0:
            weighted_avg = divide_decimal(total_value, total_qty)
        else:
            weighted_avg = Decimal("0")
        
        results.append({
            'client_id': cid,
            'symbol': sym,
            'total_buy_qty': round_decimal(total_qty),
            'total_buy_value': round_decimal(total_value),
            'weighted_avg_buy_price': weighted_avg
        })
    
    return pd.DataFrame(results)


def compute_realized_pnl_by_stock(cg_df: pd.DataFrame,
                                  client_id: str = None) -> pd.DataFrame:
    """
    Compute realized P&L per stock per client from capital gains.
    
    Args:
        cg_df: Normalized capital gains DataFrame
        client_id: Optional client filter
    
    Returns:
        DataFrame with columns: client_id, symbol, total_pnl, stcg, ltcg, num_transactions
    """
    if cg_df.empty:
        return pd.DataFrame()
    
    df = cg_df.copy()
    if client_id:
        df = df[df['client_id'] == client_id]
    
    # Group by client and symbol
    grouped = df.groupby(['client_id', 'symbol'])
    
    results = []
    
    for (cid, sym), group in grouped:
        # Total P&L
        total_pnl = sum_decimals(*group['pnl'].tolist())
        
        # STCG and LTCG
        st_rows = group[group['section'] == 'ST']
        lt_rows = group[group['section'] == 'LT']
        
        stcg = sum_decimals(*st_rows['pnl'].tolist()) if not st_rows.empty else Decimal("0")
        ltcg = sum_decimals(*lt_rows['pnl'].tolist()) if not lt_rows.empty else Decimal("0")
        
        results.append({
            'client_id': cid,
            'symbol': sym,
            'total_pnl': round_decimal(total_pnl),
            'stcg': round_decimal(stcg),
            'ltcg': round_decimal(ltcg),
            'num_transactions': len(group)
        })
    
    return pd.DataFrame(results)


def compute_client_overview(trades_df: pd.DataFrame,
                            cg_df: pd.DataFrame,
                            client_id: str) -> Dict:
    """
    Compute overview metrics for a client.
    
    Args:
        trades_df: Normalized trades DataFrame
        cg_df: Normalized capital gains DataFrame
        client_id: Client ID
    
    Returns:
        Dictionary with overview metrics
    """
    # Filter for client
    client_trades = trades_df[trades_df['client_id'] == client_id]
    client_cg = cg_df[cg_df['client_id'] == client_id]
    
    # Number of unique stocks
    stocks_traded = client_trades['symbol'].nunique() if not client_trades.empty else 0
    
    # Total realized P&L
    total_pnl = sum_decimals(*client_cg['pnl'].tolist()) if not client_cg.empty else Decimal("0")
    
    # STCG and LTCG
    st_rows = client_cg[client_cg['section'] == 'ST']
    lt_rows = client_cg[client_cg['section'] == 'LT']
    
    total_stcg = sum_decimals(*st_rows['pnl'].tolist()) if not st_rows.empty else Decimal("0")
    total_ltcg = sum_decimals(*lt_rows['pnl'].tolist()) if not lt_rows.empty else Decimal("0")
    
    # Best and worst stocks
    pnl_by_stock = compute_realized_pnl_by_stock(client_cg, client_id)
    
    if not pnl_by_stock.empty:
        # Sort by total P&L
        pnl_by_stock_sorted = pnl_by_stock.sort_values('total_pnl', ascending=False)
        
        top_5_profit = pnl_by_stock_sorted.head(5)[['symbol', 'total_pnl']].to_dict('records')
        top_5_loss = pnl_by_stock_sorted.tail(5)[['symbol', 'total_pnl']].to_dict('records')
    else:
        top_5_profit = []
        top_5_loss = []
    
    # Number of trades
    num_trades = len(client_trades)
    num_buy_trades = len(client_trades[client_trades['action'] == 'Buy'])
    num_sell_trades = len(client_trades[client_trades['action'] == 'Sell'])
    
    return {
        'client_id': client_id,
        'num_stocks': stocks_traded,
        'num_trades': num_trades,
        'num_buy_trades': num_buy_trades,
        'num_sell_trades': num_sell_trades,
        'total_realized_pnl': round_decimal(total_pnl),
        'total_stcg': round_decimal(total_stcg),
        'total_ltcg': round_decimal(total_ltcg),
        'top_5_profit_stocks': top_5_profit,
        'top_5_loss_stocks': top_5_loss
    }


def consolidate_by_isin(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Consolidate trades across brokers using ISIN as primary key.
    Fallback to (Exchange + Symbol) when ISIN is missing.
    
    Args:
        trades_df: Normalized trades DataFrame
    
    Returns:
        DataFrame with consolidation_key added
    """
    df = trades_df.copy()
    
    # Create consolidation key
    def create_key(row):
        if row['isin'] and pd.notna(row['isin']):
            return f"ISIN:{row['isin']}"
        else:
            exchange = row['exchange'] if row['exchange'] else 'UNKNOWN'
            return f"EX:{exchange}:{row['symbol']}"
    
    df['consolidation_key'] = df.apply(create_key, axis=1)
    
    return df


def compute_aggregated_metrics(trades_df: pd.DataFrame, 
                               cg_df: pd.DataFrame,
                               client_id: str) -> Dict[str, pd.DataFrame]:
    """
    Compute all aggregated metrics for a client.
    
    Args:
        trades_df: Normalized trades DataFrame
        cg_df: Normalized capital gains DataFrame
        client_id: Client ID
    
    Returns:
        Dictionary with DataFrames:
            - trade_summary_by_stock
            - capital_gains_by_stock
            - overview (as single-row DataFrame)
    """
    # Filter for client
    client_trades = trades_df[trades_df['client_id'] == client_id]
    client_cg = cg_df[cg_df['client_id'] == client_id]
    
    # Weighted average buy prices
    trade_summary = compute_weighted_avg_buy_price(client_trades)
    
    # Realized P&L by stock
    cg_summary = compute_realized_pnl_by_stock(client_cg)
    
    # Overview metrics
    overview_dict = compute_client_overview(trades_df, cg_df, client_id)
    overview_df = pd.DataFrame([overview_dict])
    
    return {
        'trade_summary_by_stock': trade_summary,
        'capital_gains_by_stock': cg_summary,
        'overview': overview_df
    }


def get_all_clients(trades_df: pd.DataFrame, cg_df: pd.DataFrame) -> List[str]:
    """
    Get list of all unique client IDs.
    
    Args:
        trades_df: Normalized trades DataFrame
        cg_df: Normalized capital gains DataFrame
    
    Returns:
        List of client IDs
    """
    clients = set()
    
    if not trades_df.empty:
        clients.update(trades_df['client_id'].unique())
    
    if not cg_df.empty:
        clients.update(cg_df['client_id'].unique())
    
    return sorted(list(clients))
