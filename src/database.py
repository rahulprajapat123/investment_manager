"""
Database module for Supabase integration.
Provides functions to store and retrieve portfolio data.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
use_database = os.getenv("USE_DATABASE", "false").lower() == "true"

supabase: Optional[Client] = None

def init_supabase():
    """Initialize Supabase client."""
    global supabase
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        return supabase
    return None

def is_database_enabled():
    """Check if database mode is enabled."""
    return use_database and supabase_url and supabase_key

# ===== CLIENT OPERATIONS =====

def get_all_clients(page: int = 1, page_size: int = 50) -> Dict:
    """
    Get all clients with pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of clients per page
    
    Returns:
        Dict with clients list and metadata
    """
    if not supabase:
        init_supabase()
    
    offset = (page - 1) * page_size
    
    # Get total count
    count_response = supabase.table("clients").select("*", count="exact").execute()
    total_count = count_response.count if hasattr(count_response, 'count') else 0
    
    # Get paginated data
    response = supabase.table("clients")\
        .select("*, trades(count), capital_gains(count)")\
        .range(offset, offset + page_size - 1)\
        .order("created_at", desc=True)\
        .execute()
    
    clients = []
    for client in response.data:
        clients.append({
            "client_id": client["client_id"],
            "has_report": client["has_report"],
            "report_date": client["report_generated_at"],
            "data_files_count": client["data_files_count"],
            "created_at": client["created_at"]
        })
    
    return {
        "clients": clients,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }

def create_or_update_client(client_id: str, metadata: Dict = None) -> Dict:
    """Create or update a client."""
    if not supabase:
        init_supabase()
    
    data = {
        "client_id": client_id,
        "updated_at": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    # Try to update first, if not exists, insert
    response = supabase.table("clients").upsert(data).execute()
    return response.data[0] if response.data else {}

def delete_client(client_id: str) -> bool:
    """Delete a client and all associated data (cascades)."""
    if not supabase:
        init_supabase()
    
    response = supabase.table("clients").delete().eq("client_id", client_id).execute()
    return len(response.data) > 0

# ===== TRADES OPERATIONS =====

def save_trades(client_id: str, trades_df: pd.DataFrame) -> int:
    """
    Save trades to database.
    
    Args:
        client_id: Client identifier
        trades_df: DataFrame with trade data
    
    Returns:
        Number of trades saved
    """
    if not supabase or trades_df.empty:
        return 0
        
    init_supabase()
    
    # Convert DataFrame to list of dicts
    trades_list = []
    for _, row in trades_df.iterrows():
        trade = {
            "client_id": client_id,
            "broker": str(row.get("broker", "")),
            "symbol": str(row.get("symbol", "")),
            "action": str(row.get("action", "")),
            "trade_date": str(row.get("trade_date", "")),
            "qty": float(row.get("qty", 0)),
            "price": float(row.get("price", 0)),
            "amount": float(row.get("amount", 0)),
            "fees": float(row.get("fees", 0)),
            "file_type": str(row.get("file_type", "trade_book"))
        }
        trades_list.append(trade)
    
    # Batch insert
    response = supabase.table("trades").insert(trades_list).execute()
    return len(response.data) if response.data else 0

def get_trades(client_id: str) -> pd.DataFrame:
    """Get all trades for a client."""
    if not supabase:
        init_supabase()
    
    response = supabase.table("trades")\
        .select("*")\
        .eq("client_id", client_id)\
        .execute()
    
    if not response.data:
        return pd.DataFrame()
    
    return pd.DataFrame(response.data)

# ===== CAPITAL GAINS OPERATIONS =====

def save_capital_gains(client_id: str, cg_df: pd.DataFrame) -> int:
    """
    Save capital gains to database.
    
    Args:
        client_id: Client identifier
        cg_df: DataFrame with capital gains data
    
    Returns:
        Number of records saved
    """
    if not supabase or cg_df.empty:
        return 0
        
    init_supabase()
    
    # Convert DataFrame to list of dicts
    cg_list = []
    for _, row in cg_df.iterrows():
        cg = {
            "client_id": client_id,
            "broker": str(row.get("broker", "")),
            "symbol": str(row.get("symbol", "")),
            "buy_date": str(row.get("buy_date", "")) if pd.notna(row.get("buy_date")) else None,
            "sell_date": str(row.get("sell_date", "")),
            "qty": float(row.get("qty", 0)),
            "buy_price": float(row.get("buy_price", 0)) if pd.notna(row.get("buy_price")) else None,
            "sell_price": float(row.get("sell_price", 0)),
            "cost_basis": float(row.get("cost_basis", 0)) if pd.notna(row.get("cost_basis")) else None,
            "proceeds": float(row.get("proceeds", 0)),
            "gain_loss": float(row.get("gain_loss", 0)) if pd.notna(row.get("gain_loss")) else None,
            "holding_period": str(row.get("holding_period", "")) if pd.notna(row.get("holding_period")) else None
        }
        cg_list.append(cg)
    
    # Batch insert
    response = supabase.table("capital_gains").insert(cg_list).execute()
    return len(response.data) if response.data else 0

def get_capital_gains(client_id: str) -> pd.DataFrame:
    """Get all capital gains for a client."""
    if not supabase:
        init_supabase()
    
    response = supabase.table("capital_gains")\
        .select("*")\
        .eq("client_id", client_id)\
        .execute()
    
    if not response.data:
        return pd.DataFrame()
    
    return pd.DataFrame(response.data)

# ===== REPORT OPERATIONS =====

def mark_report_generated(client_id: str, file_path: str) -> bool:
    """Mark that a report has been generated for a client."""
    if not supabase:
        init_supabase()
    
    # Update client
    supabase.table("clients").update({
        "has_report": True,
        "report_generated_at": datetime.now().isoformat()
    }).eq("client_id", client_id).execute()
    
    # Insert report record
    supabase.table("reports").insert({
        "client_id": client_id,
        "file_path": file_path,
        "status": "completed",
        "generated_at": datetime.now().isoformat()
    }).execute()
    
    return True

# ===== JOB QUEUE OPERATIONS =====

def create_job(job_id: str, client_id: str, job_type: str) -> Dict:
    """Create a job entry in the database."""
    if not supabase:
        init_supabase()
    
    job_data = {
        "job_id": job_id,
        "client_id": client_id,
        "job_type": job_type,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    response = supabase.table("job_queue").insert(job_data).execute()
    return response.data[0] if response.data else {}

def update_job_status(job_id: str, status: str, error_message: str = None, result: Dict = None) -> bool:
    """Update job status."""
    if not supabase:
        init_supabase()
    
    update_data = {
        "status": status,
        "completed_at": datetime.now().isoformat()
    }
    
    if status == "processing":
        update_data["started_at"] = datetime.now().isoformat()
    
    if error_message:
        update_data["error_message"] = error_message
    
    if result:
        update_data["result"] = result
    
    response = supabase.table("job_queue").update(update_data).eq("job_id", job_id).execute()
    return len(response.data) > 0

def get_job(job_id: str) -> Dict:
    """Get job status."""
    if not supabase:
        init_supabase()
    
    response = supabase.table("job_queue").select("*").eq("job_id", job_id).execute()
    return response.data[0] if response.data else {}
