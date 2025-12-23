# Portfolio Analytics Platform

A modern web application for portfolio data ingestion, analysis, and report generation built with **FastAPI** and **React**.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) - RESTful API for data processing
- **Frontend**: React + Vite + Ant Design - Modern responsive UI
- **Data Processing**: Python pipeline (ingestion → normalization → validation → aggregation → reporting)

## 📁 Project Structure

```
portfolio-analytics/
├── backend/               # FastAPI backend
│   ├── main.py           # API endpoints
│   └── requirements.txt  # Backend dependencies
├── frontend/             # React frontend
│   ├── src/
│   │   ├── pages/       # Dashboard, Upload, Reports
│   │   ├── App.jsx      # Main app component
│   │   └── main.jsx     # Entry point
│   ├── package.json     # Frontend dependencies
│   └── vite.config.js   # Vite configuration
├── src/                  # Core data processing modules
│   ├── ingestion.py     # Data ingestion
│   ├── normalizer.py    # Data normalization
│   ├── validator.py     # Data validation
│   ├── aggregator.py    # Metric aggregation
│   └── report_generator.py  # Excel report generation
├── data/                 # Client data storage
│   └── C001/            # Client folders
│       ├── Charles_Schwab/
│       ├── Fidelity/
│       └── ...
├── reports/              # Generated reports
└── requirements.txt      # Python dependencies
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Git

### 1. Clone and Setup Python Environment

```powershell
cd "c:\Users\praja\Desktop\demo investment project"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Setup Backend

```powershell
# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### 3. Setup Frontend

```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Return to root
cd ..
```

## 🎯 Running the Application

### Start Backend (Terminal 1)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate

# Run FastAPI server
python backend\main.py
```

Backend will run on: **http://localhost:8000**

### Start Frontend (Terminal 2)

```powershell
# Navigate to frontend
cd frontend

# Start development server
npm run dev
```

Frontend will run on: **http://localhost:3000**

## 🌐 Usage

1. **Open Browser**: Navigate to http://localhost:3000

2. **Upload Data**:
   - Click "Upload Data" in sidebar
   - Enter Client ID (e.g., C005 or just 5)
   - Select Broker from dropdown
   - Upload Excel files (trade books, capital gains, holdings)
   - Click "Upload Files"

3. **Generate Reports**:
   - Go to "Dashboard"
   - Find your client in the table
   - Click "Generate Report" button
   - Wait for processing to complete

4. **Download Reports**:
   - Go to "Reports" page
   - Click "Download" button for any client
   - Report downloads as Excel file

## 📊 Features

### Dashboard
- View all clients at a glance
- See report generation status
- Track data files per client
- One-click report generation
- Real-time processing status

### Upload Interface
- Drag-and-drop file upload
- Multi-file support
- Broker selection
- Client ID validation
- File type validation (Excel only)

### Reports Management
- View all generated reports
- Search and filter capabilities
- Download reports
- Sort by date, status, client ID

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/clients` | List all clients |
| GET | `/api/brokers` | List supported brokers |
| POST | `/api/upload` | Upload client files |
| POST | `/api/process/{client_id}` | Generate report for client |
| GET | `/api/jobs/{job_id}` | Check job status |
| GET | `/api/reports/{client_id}` | Download client report |
| DELETE | `/api/clients/{client_id}` | Delete client data |

## 📦 Supported Brokers

- Charles Schwab
- Fidelity
- Groww
- HDFC Bank
- ICICI Direct
- Zerodha

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Pandas** - Data processing
- **OpenPyXL** - Excel file handling
- **Pandera** - Data validation

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **Ant Design** - UI component library
- **Axios** - HTTP client
- **React Router** - Navigation

## 🛠️ Development

### Backend Development

```powershell
# Run with auto-reload
python backend\main.py
```

API docs available at: http://localhost:8000/docs

### Frontend Development

```powershell
cd frontend
npm run dev
```

Hot-reload enabled automatically

### Build for Production

```powershell
# Build frontend
cd frontend
npm run build

# Preview production build
npm run preview
```

## 📝 Data Format

Upload Excel files should contain:
- **Trade Book**: Date, Symbol, Action (Buy/Sell), Quantity, Price
- **Capital Gains**: Symbol, Buy Date, Sell Date, Gain/Loss
- **Holdings**: Symbol, Quantity, Current Price

## 🐛 Troubleshooting

### Port Already in Use

**Backend (8000)**:
```powershell
# Find process using port
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
```

**Frontend (3000)**:
```powershell
# Find process using port
netstat -ano | findstr :3000
# Kill process
taskkill /PID <PID> /F
```

### CORS Errors
- Ensure backend is running on port 8000
- Check CORS middleware in `backend/main.py`

### Upload Fails
- Verify file is Excel format (.xlsx or .xls)
- Check client ID format (C001 or just 1)
- Ensure broker is selected

## 📈 Future Enhancements

- [ ] User authentication (JWT)
- [ ] Redis/Celery for async tasks
- [ ] Real-time WebSocket updates
- [ ] Database integration (PostgreSQL)
- [ ] Docker containerization
- [ ] Advanced analytics dashboard
- [ ] Email notifications
- [ ] Multi-user support

## 📄 License

Proprietary - All rights reserved

## 👥 Support

For issues or questions, contact the development team.

---

**Built with ❤️ using FastAPI and React**
