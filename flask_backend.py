"""
Portfolio Analytics Backend - Flask Version (Windows Stable)
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
from pathlib import Path
from datetime import datetime
import uuid
import shutil

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from main import run_pipeline

app = Flask(__name__)
CORS(app)

# Directories
DATA_DIR = project_root / "data"
REPORTS_DIR = project_root / "reports"
TEMP_DIR = project_root / "temp_uploads"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# In-memory job storage
jobs = {}

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "status": "healthy",
        "service": "Portfolio Analytics API",
        "version": "1.0.0"
    })

@app.route('/api/clients', methods=['GET'])
def get_clients():
    try:
        clients = []
        
        if DATA_DIR.exists():
            for client_dir in DATA_DIR.iterdir():
                if client_dir.is_dir() and client_dir.name.startswith('C'):
                    client_id = client_dir.name
                    report_path = REPORTS_DIR / f"{client_id}_portfolio_report.xlsx"
                    # Also check for old naming convention
                    if not report_path.exists():
                        report_path = REPORTS_DIR / f"{client_id}_portfolio.xlsx"
                    has_report = report_path.exists()
                    
                    data_files = []
                    for broker_dir in client_dir.iterdir():
                        if broker_dir.is_dir():
                            files = list(broker_dir.glob("*.xlsx"))
                            data_files.extend([f.name for f in files])
                    
                    clients.append({
                        "client_id": client_id,
                        "has_report": has_report,
                        "data_files_count": len(data_files),
                        "brokers": [d.name for d in client_dir.iterdir() if d.is_dir()],
                        "report_date": datetime.fromtimestamp(report_path.stat().st_mtime).isoformat() if has_report else None
                    })
        
        return jsonify({"clients": clients, "total": len(clients)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    try:
        client_id = request.form.get('client_id')
        broker = request.form.get('broker', 'Unknown_Platform')
        
        if not client_id:
            return jsonify({"error": "Client ID is required"}), 400
        
        if not broker:
            return jsonify({"error": "Broker/Platform is required"}), 400
        
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files')
        
        if not client_id.startswith('C'):
            client_id = f"C{client_id.zfill(3)}"
        
        # Use the provided broker name instead of hardcoded "Uploaded_Files"
        client_dir = DATA_DIR / client_id / broker
        client_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            if file.filename and file.filename.endswith(('.xlsx', '.xls', '.csv')):
                filename = secure_filename(file.filename)
                file_path = client_dir / filename
                file.save(file_path)
                
                uploaded_files.append({
                    "filename": filename,
                    "size": file_path.stat().st_size,
                    "path": str(file_path)
                })
        
        return jsonify({
            "success": True,
            "client_id": client_id,
            "broker": broker,
            "files": uploaded_files,
            "message": f"Successfully uploaded {len(uploaded_files)} files for {client_id} ({broker})"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/process/<client_id>', methods=['POST'])
def process_client(client_id):
    try:
        client_dir = DATA_DIR / client_id
        if not client_dir.exists():
            return jsonify({"error": f"Client {client_id} not found"}), 404
        
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "job_id": job_id,
            "client_id": client_id,
            "status": "processing",
            "created_at": datetime.now().isoformat()
        }
        
        # Run pipeline synchronously
        try:
            success = run_pipeline(
                data_dir=str(DATA_DIR),
                output_dir=str(REPORTS_DIR),
                fail_on_validation=False
            )
            
            if success:
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["result"] = {
                    "report_path": str(REPORTS_DIR / f"{client_id}_portfolio_report.xlsx"),
                    "message": f"Successfully generated report for {client_id}"
                }
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "Pipeline execution failed"
            
            jobs[job_id]["completed_at"] = datetime.now().isoformat()
        except Exception as e:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = str(e)
            jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        return jsonify(jobs[job_id])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(jobs[job_id])

@app.route('/api/reports/<client_id>', methods=['GET'])
def download_report(client_id):
    try:
        report_path = REPORTS_DIR / f"{client_id}_portfolio_report.xlsx"
        # Fallback to old naming convention
        if not report_path.exists():
            report_path = REPORTS_DIR / f"{client_id}_portfolio.xlsx"
        
        if not report_path.exists():
            return jsonify({"error": f"Report not found for client {client_id}"}), 404
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"{client_id}_portfolio.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    try:
        client_dir = DATA_DIR / client_id
        report_path = REPORTS_DIR / f"{client_id}_portfolio_report.xlsx"
        # Fallback to old naming
        if not report_path.exists():
            report_path = REPORTS_DIR / f"{client_id}_portfolio.xlsx"
        
        deleted_items = []
        
        if client_dir.exists():
            shutil.rmtree(client_dir)
            deleted_items.append("data")
        
        if report_path.exists():
            report_path.unlink()
            deleted_items.append("report")
        
        if not deleted_items:
            return jsonify({"error": f"Client {client_id} not found"}), 404
        
        return jsonify({
            "success": True,
            "client_id": client_id,
            "deleted": deleted_items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Portfolio Analytics Backend - Flask Server")
    print("=" * 60)
    print("Server: http://127.0.0.1:5000")
    print("Status: Running")
    print("Press CTRL+C to stop")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
