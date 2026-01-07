"""
RQ Worker module for background job processing.
Handles async report generation tasks.
"""
import os
import sys
from pathlib import Path
from redis import Redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Redis connection
redis_url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(redis_url)

# Create queue
task_queue = Queue("portfolio_tasks", connection=redis_conn)

def process_client_report(client_id: str, data_dir: str, output_dir: str):
    """
    Background job to process client report.
    
    Args:
        client_id: Client identifier
        data_dir: Data directory path
        output_dir: Output directory for reports
    
    Returns:
        Dict with success status and message
    """
    from main import run_pipeline
    from database import mark_report_generated, is_database_enabled, save_trades, save_capital_gains
    from normalizer import normalize_all_files
    from ingestion import ingest_all_files
    
    try:
        # Check if database mode is enabled
        if is_database_enabled():
            # Process and save to database
            ingested_files = ingest_all_files(data_dir)
            if not ingested_files:
                return {"success": False, "error": "No files found"}
            
            normalized_data = normalize_all_files(ingested_files)
            trades_df = normalized_data['trades']
            cg_df = normalized_data['capital_gains']
            
            # Save to database
            trades_saved = save_trades(client_id, trades_df)
            cg_saved = save_capital_gains(client_id, cg_df)
            
            # Generate report
            success = run_pipeline(data_dir, output_dir, fail_on_validation=False)
            
            if success:
                report_path = Path(output_dir) / f"{client_id}_portfolio_report.xlsx"
                mark_report_generated(client_id, str(report_path))
                
                return {
                    "success": True,
                    "message": f"Report generated for {client_id}",
                    "trades_saved": trades_saved,
                    "capital_gains_saved": cg_saved
                }
        else:
            # File-based mode (original)
            success = run_pipeline(data_dir, output_dir, fail_on_validation=False)
            
            if success:
                return {
                    "success": True,
                    "message": f"Report generated for {client_id}"
                }
        
        return {"success": False, "error": "Report generation failed"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def enqueue_report_generation(client_id: str, data_dir: str, output_dir: str):
    """
    Enqueue a report generation job.
    
    Args:
        client_id: Client identifier
        data_dir: Data directory path
        output_dir: Output directory for reports
    
    Returns:
        Job object with job_id
    """
    job = task_queue.enqueue(
        process_client_report,
        client_id,
        data_dir,
        output_dir,
        job_timeout='10m',  # 10 minute timeout
        result_ttl=86400    # Keep result for 24 hours
    )
    return job

def get_job_status(job_id: str):
    """
    Get the status of a job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        Dict with job status
    """
    from rq.job import Job
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        status_map = {
            'queued': 'pending',
            'started': 'processing',
            'finished': 'completed',
            'failed': 'failed'
        }
        
        return {
            "job_id": job.id,
            "status": status_map.get(job.get_status(), job.get_status()),
            "result": job.result if job.is_finished else None,
            "error": str(job.exc_info) if job.is_failed else None,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None
        }
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "not_found",
            "error": str(e)
        }

def start_worker():
    """Start the RQ worker."""
    print("="*80)
    print("RQ Worker - Portfolio Analytics")
    print("="*80)
    print(f"Redis URL: {redis_url}")
    print(f"Queue: portfolio_tasks")
    print("Listening for jobs...")
    print("="*80)
    
    with Connection(redis_conn):
        worker = Worker(['portfolio_tasks'], connection=redis_conn)
        worker.work()

if __name__ == '__main__':
    start_worker()
