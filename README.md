# Portfolio Analytics Platform

A modern web application for multi-broker portfolio data ingestion, analysis, and comprehensive report generation built with **Flask** and **React**.

## ✨ Latest Updates (Jan 2026)

### 🎯 Multi-Platform Upload Feature
- **Simultaneous multi-broker file upload** - Upload files from multiple platforms at once
- **Auto-detection of brokers** from filenames (Zerodha, Groww, HDFC, ICICI, Schwab, Fidelity, etc.)
- **Manual broker assignment** via intuitive file-broker mapping table
- **Automatic folder organization** by broker

### 🐛 Critical Fixes
- **Platform count accuracy** - Fixed issue where platform count always showed 1, now correctly counts all brokers from trades data
- **Multi-broker stock tracking** - Added "Holdings by Broker" sheet showing positions split by platform
- **Broker detection improvements** - Enhanced extraction from file paths and names
- **Decimal precision verified** - All numeric calculations use Decimal for accuracy

### 📊 Enhanced Reports
- New **"Holdings by Broker"** sheet - See each stock's position on each platform separately
- **Platform breakdown** in Summary sheet - Shows trades and stocks per broker
- **Aggregated + detailed views** - Both portfolio-level and broker-level analysis
- **Accurate platform metrics** - Counts all brokers used, not just current holdings

## 🏗️ Architecture

- **Backend**: Flask (Python) - RESTful API for data processing and file handling
- **Frontend**: React + Vite + Ant Design - Modern responsive UI with multi-file upload
- **Data Processing**: Python pipeline with Decimal precision (ingestion → normalization → validation → aggregation → reporting)
- **Multi-Broker Support**: Automatic broker detection and separate folder organization

## 📁 Project Structure

```
portfolio-analytics/
├── flask_backend.py      # Flask API server
├── frontend/             # React frontend
│   ├── src/
│   │   ├── pages/       
│   │   │   ├── Dashboard.jsx    # Client management & report generation
│   │   │   └── Upload.jsx       # Multi-platform file upload with broker mapping
│   │   ├── App.jsx      # Main app component
│   │   └── main.jsx     # Entry point
│   ├── package.json     # Frontend dependencies
│   └── vite.config.js   # Vite configuration
├── src/                  # Core data processing modules
│   ├── ingestion.py     # Multi-broker data ingestion
│   ├── normalizer.py    # Data normalization with broker tracking
│   ├── validator.py     # Data validation
│   ├── aggregator.py    # Metric aggregation
│   ├── report_generator.py      # Excel report generation with multi-broker sheets
│   └── holdings_multibroker.py  # Multi-broker position tracking
├── data/                 # Client data storage (organized by broker)
│   └── C001/            # Client folders
│       ├── Charles_Schwab/      # Files uploaded for this broker
│       ├── Fidelity/            # Files uploaded for this broker
│       └── Groww/               # Files uploaded for this broker
├── reports/              # Generated Excel reports
├── verify_numeric_calculations.py    # Verification script for calculation accuracy
├── verify_c004_completeness.py      # Script to verify aggregation completeness
├── test_multiplatform.py            # Multi-platform upload testing
├── MULTIPLATFORM_UPLOAD_GUIDE.md    # Detailed guide for multi-platform features
├── C004_VERIFICATION_REPORT.md      # Sample verification report
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
.\venv311\Scripts\Activate

# Run Flask server
python flask_backend.py
```

Backend will run on: **http://127.0.0.1:5000**

### Start Frontend (Terminal 2)

```powershell
# Navigate to frontend
cd frontend

# Start development server
npm run dev
```

Frontend will run on: **http://localhost:3000**

## 🌐 Usage

### Multi-Platform Upload (NEW!)

1. **Open Browser**: Navigate to http://localhost:3000

2. **Upload Data from Multiple Brokers**:
   - Click "Upload Data" in sidebar
   - Enter Client ID (e.g., C003)
   - **Select multiple files from different platforms at once**
   - System auto-detects brokers from filenames (or assign manually)
   - Review file-broker mapping table
   - Click "Upload X files from Y platforms"

3. **Generate Aggregated Reports**:
   - Go to "Dashboard"
   - Find your client in the table
   - Click "Generate Report" button
   - Wait for processing to complete

4. **Download Reports**:
   - Go to "Reports" page
   - Click "Download" button for any client
   - Report downloads as Excel file

## 📊 Key Features

### Multi-Platform Upload ⭐ NEW
- **Simultaneous upload from multiple brokers** - No need to upload each platform separately
- **Auto-detection** - System recognizes broker from filename
- **File-Broker mapping table** - Visual interface to assign each file to its broker
- **Batch processing** - All platforms processed together
- **Smart organization** - Files automatically organized in broker-specific folders

### Advanced Dashboard
- View all clients at a glance
- See report generation status
- **Platform count** - Shows correct number of brokers used
- Track data files per client and per broker
- One-click report generation with job tracking
- Real-time processing status

### Enhanced Reports
- **Holdings Sheet** - Aggregated positions across all brokers
- **Holdings by Broker Sheet** ⭐ NEW - Detailed breakdown per platform
- **Summary Sheet** - Platform count, breakdown, and key metrics
- **Allocations Sheet** - Asset allocation across brokers
- **Calculations Sheet** - All trades and capital gains with broker info

### Upload Interface
- Drag-and-drop file upload
- Multi-file support (upload 10+ files at once)
- **Broker auto-detection and manual assignment**
- Client ID validation
- File type validation (Excel, CSV)
- Upload progress tracking

### Data Accuracy
- **Decimal precision** - All calculations use Decimal arithmetic
- **Comprehensive validation** - Data quality checks at every step
- **Verification scripts** - Tools to verify calculation accuracy
- **Multi-broker aggregation** - Correct handling of stocks across platforms

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/api/clients` | List all clients with platform counts |
| POST | `/api/upload` | Upload files with `client_id` and `broker` params |
| POST | `/api/generate-report/{client_id}` | Process all data and generate Excel report |
| GET | `/api/report/{client_id}` | Download generated Excel report |
| DELETE | `/api/client/{client_id}` | Delete client data and reports |

### Upload Endpoint Details
```json
POST /api/upload
Content-Type: multipart/form-data

Parameters:
- client_id: string (e.g., "C001")
- broker: string (e.g., "Charles_Schwab")
- files: files[] (tradebook.csv, holdings.csv)
```

## 📦 Supported Brokers

The system auto-detects these brokers from filenames:

- **Charles Schwab** - Detects "schwab", "charles"
- **Fidelity** - Detects "fidelity"
- **Groww** - Detects "groww"
- **HDFC Bank** - Detects "hdfc"
- **ICICI Direct** - Detects "icici"
- **Zerodha** - Detects "zerodha"
- **Upstox** - Detects "upstox"
- **Angel One** - Detects "angel"

Manual assignment available for any broker name.

## 🔧 Technology Stack

### Backend
- **Flask** - Python web framework
- **Pandas** - Data processing with Decimal precision
- **OpenPyXL** - Excel report generation
- **Python 3.14.0** - Runtime environment
- **Decimal Arithmetic** - High-precision financial calculations

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Ant Design** - UI component library
- **Axios** - HTTP client
- **React Router DOM** - Navigation

## 🛠️ Development

### Backend Development

```powershell
# Activate virtual environment
.\venv311\Scripts\activate

# Run Flask server
python flask_backend.py
```

Server runs at: http://127.0.0.1:5000

### Frontend Development

```powershell
cd frontend
npm run dev
```

Dev server runs at: http://localhost:3000 with hot-reload

### Build for Production

```powershell
# Build frontend
cd frontend
npm run build

# Preview production build
npm run preview
```

## 🧪 Testing & Verification

### Verification Scripts
The project includes comprehensive testing tools:

- `verify_numeric_calculations.py` - Check Decimal precision in all calculations
- `verify_c004_completeness.py` - Verify aggregation accuracy for C004 client
- `test_multiplatform.py` - Test multi-broker processing
- `comprehensive_verify.py` - Full system verification
- Additional scripts in root directory for debugging specific issues

### Run Verification
```powershell
# Verify calculations
python verify_numeric_calculations.py

# Verify C004 aggregation
python verify_c004_completeness.py

# Test multi-platform upload
python test_multiplatform.py
```

## 📝 Data Format

### Required Files Per Broker
Each broker upload should include:

1. **Trade Book** (tradebook.csv or tradebook.xlsx):
   - Columns: Date, Symbol, Action (Buy/Sell), Quantity, Price
   - Action can be: BUY, SELL, buy, sell

2. **Holdings** (holdings.csv or holdings.xlsx):
   - Columns: Symbol, Quantity, Current Price
   - Represents current open positions

### CSV Format Support
Both CSV and Excel formats are supported. CSV files use standard parsing with automatic delimiter detection.

### File Naming
Files are auto-organized by broker. You can name them:
- `tradebook_zerodha.csv` → Auto-detected as Zerodha
- `holdings_groww.xlsx` → Auto-detected as Groww
- Or manually assign via the upload interface

## 🐛 Troubleshooting

### Port Already in Use

**Backend (5000)**:
```powershell
# Find process using port
netstat -ano | findstr :5000
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

### Connection Refused (ERR_CONNECTION_REFUSED)
- Ensure Flask backend is running: `python flask_backend.py`
- Check backend console for errors
- Verify backend is accessible at http://127.0.0.1:5000

### Multi-Platform Upload Issues
- Ensure all files are CSV or Excel format
- Check that each file is assigned to a broker in the table
- Verify broker names don't contain special characters
- Check browser console for detailed error messages

### Report Generation Failures
- Verify all required files are uploaded (tradebook + holdings)
- Check data format matches expected columns
- Review backend console for detailed error messages
- Use verification scripts to check data integrity

### Platform Count Shows Wrong Number
This was a known bug (fixed). If you still see issues:
- Regenerate the report
- Check that `client_trades['broker'].nunique()` is used in report_generator.py
- Verify broker names are consistent across files

## 📈 Recent Enhancements

### ✅ Completed Features
- [x] Multi-broker simultaneous upload with file-broker mapping
- [x] Auto-detection of brokers from filenames
- [x] Platform count accuracy fix (uses trades data instead of holdings)
- [x] "Holdings by Broker" detailed sheet in reports
- [x] CSV file format support
- [x] Comprehensive verification scripts for data accuracy
- [x] Decimal precision for all financial calculations
- [x] Enhanced broker extraction logic

### 🚀 Future Enhancements
- [ ] User authentication (JWT)
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Real-time WebSocket updates for report generation
- [ ] Advanced analytics and charting
- [ ] Docker containerization
- [ ] Tax optimization recommendations
- [ ] Historical performance tracking
- [ ] Email notifications
- [ ] Multi-user support

## 📄 License

Proprietary - All rights reserved

## 👥 Support

For issues or questions, contact the development team.

---

**Built with ❤️ using FastAPI and React**
