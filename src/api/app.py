"""
Flask API for the Investment Platform.
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config import Config
from src.utils.database import get_database
from src.utils.helpers import setup_logging, validate_ticker, format_currency, format_percentage
from src.models.predict import StockPredictor
from src.models.backtest import Backtester
from src.processors.document_processor import DocumentProcessor
from src.processors.report_generator import ReportGenerator

# Get the project root directory
project_root = str(Path(__file__).parent.parent.parent)
static_folder = os.path.join(project_root, 'static')

# Initialize Flask app
app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
CORS(app)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize database and predictor
db = get_database()
predictor = None

# Initialize document processor and report generator
doc_processor = DocumentProcessor()
report_generator = ReportGenerator()

# Try to load predictor
try:
    if Config.ENABLE_ML_PREDICTIONS:
        predictor = StockPredictor()
        logger.info("ML predictor loaded successfully")
except Exception as e:
    logger.warning(f"Could not load ML predictor: {e}")

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xlsx', 'xls', 'txt', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'ml_enabled': predictor is not None,
        'database': 'connected'
    })


@app.route('/api/portfolio/<int:client_id>')
def get_portfolio(client_id):
    """
    Get portfolio for a client.
    
    Args:
        client_id: Client ID
        
    Returns:
        Portfolio data with current values
    """
    try:
        portfolio = db.get_portfolio_value(client_id)
        
        # Format response
        response = {
            'client_id': client_id,
            'total_value': format_currency(portfolio['total_value']),
            'total_value_raw': portfolio['total_value'],
            'total_cost': format_currency(portfolio['total_cost']),
            'total_gain_loss': format_currency(portfolio['total_gain_loss']),
            'total_gain_loss_pct': format_percentage(portfolio['total_gain_loss_pct']),
            'positions': [
                {
                    'ticker': p['ticker'],
                    'shares': p['shares'],
                    'cost_basis': format_currency(p['cost_basis']),
                    'current_price': format_currency(p['current_price']),
                    'position_value': format_currency(p['position_value']),
                    'gain_loss': format_currency(p['gain_loss']),
                    'gain_loss_pct': format_percentage(p['gain_loss_pct'])
                }
                for p in portfolio['positions']
            ]
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock/<ticker>')
def get_stock(ticker):
    """
    Get current stock information.
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Stock price and basic info
    """
    try:
        ticker = ticker.upper()
        
        if not validate_ticker(ticker):
            return jsonify({'error': 'Invalid ticker'}), 400
        
        # Get price data
        prices = db.load_daily_prices(ticker=ticker)
        
        if prices.empty:
            return jsonify({'error': f'No data found for {ticker}'}), 404
        
        # Get latest data
        latest = prices.iloc[-1]
        previous = prices.iloc[-2] if len(prices) > 1 else latest
        
        # Calculate daily change
        daily_change = latest['close'] - previous['close']
        daily_change_pct = (daily_change / previous['close']) * 100
        
        # Get 30-day stats
        recent_30d = prices.tail(30)
        high_30d = recent_30d['high'].max()
        low_30d = recent_30d['low'].min()
        avg_volume_30d = recent_30d['volume'].mean()
        
        response = {
            'ticker': ticker,
            'date': str(latest['date']),
            'price': {
                'current': latest['close'],
                'open': latest['open'],
                'high': latest['high'],
                'low': latest['low'],
                'previous_close': previous['close']
            },
            'change': {
                'amount': daily_change,
                'percent': daily_change_pct,
                'formatted': format_percentage(daily_change_pct)
            },
            'volume': {
                'current': int(latest['volume']),
                'avg_30d': int(avg_volume_30d)
            },
            'range_30d': {
                'high': high_30d,
                'low': low_30d
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting stock data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict/<ticker>')
def predict_stock(ticker):
    """
    Get ML prediction for a stock.
    
    Args:
        ticker: Stock ticker
        
    Returns:
        Prediction and recommendation
    """
    try:
        if not predictor:
            return jsonify({'error': 'ML predictions not available'}), 503
        
        ticker = ticker.upper()
        
        if not validate_ticker(ticker):
            return jsonify({'error': 'Invalid ticker'}), 400
        
        # Get prediction
        result = predictor.predict(ticker)
        
        response = {
            'ticker': result['ticker'],
            'date': str(result['date']),
            'current_price': result['current_price'],
            'prediction': {
                'direction': result['prediction'],
                'probability_up': f"{result['probability_up']:.1%}",
                'probability_down': f"{result['probability_down']:.1%}",
                'probability_up_raw': result['probability_up'],
                'probability_down_raw': result['probability_down']
            },
            'recommendation': {
                'action': result['recommendation']['action'],
                'strength': result['recommendation']['strength'],
                'confidence': f"{result['recommendation']['confidence']:.1%}",
                'confidence_raw': result['recommendation']['confidence']
            },
            'key_features': result['features']
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error predicting stock: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/recommendations')
def get_recommendations():
    """
    Get top stock recommendations.
    
    Query params:
        action: BUY/SELL/HOLD (default: BUY)
        limit: Number of recommendations (default: 5)
        
    Returns:
        List of top recommendations
    """
    try:
        if not predictor:
            return jsonify({'error': 'ML predictions not available'}), 503
        
        action = request.args.get('action', 'BUY').upper()
        limit = int(request.args.get('limit', 5))
        
        # Get all available tickers
        tickers = db.load_daily_prices()['ticker'].unique().tolist()
        
        # Get recommendations
        recommendations = predictor.get_top_recommendations(
            tickers=tickers,
            top_n=limit,
            action=action
        )
        
        # Format response
        response = {
            'action': action,
            'count': len(recommendations),
            'recommendations': [
                {
                    'rank': i + 1,
                    'ticker': rec['ticker'],
                    'current_price': rec['current_price'],
                    'prediction': rec['prediction'],
                    'action': rec['recommendation']['action'],
                    'strength': rec['recommendation']['strength'],
                    'confidence': f"{rec['recommendation']['confidence']:.1%}",
                    'confidence_raw': rec['recommendation']['confidence']
                }
                for i, rec in enumerate(recommendations)
            ]
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/top-stocks')
def get_top_stocks():
    """
    Get top performing stocks.
    
    Query params:
        period: 1d/5d/30d (default: 1d)
        limit: Number of stocks (default: 10)
        
    Returns:
        List of top performers
    """
    try:
        period = request.args.get('period', '1d')
        limit = int(request.args.get('limit', 10))
        
        # Map period to days
        period_map = {'1d': 1, '5d': 5, '30d': 30}
        days = period_map.get(period, 1)
        
        # Get all prices
        all_prices = db.load_daily_prices()
        
        # Calculate returns for each ticker
        results = []
        for ticker in all_prices['ticker'].unique():
            ticker_prices = all_prices[all_prices['ticker'] == ticker].sort_values('date')
            
            if len(ticker_prices) < days + 1:
                continue
            
            current_price = ticker_prices.iloc[-1]['close']
            past_price = ticker_prices.iloc[-(days + 1)]['close']
            
            return_pct = ((current_price - past_price) / past_price) * 100
            
            results.append({
                'ticker': ticker,
                'current_price': current_price,
                'return': return_pct,
                'return_formatted': format_percentage(return_pct)
            })
        
        # Sort by return
        results.sort(key=lambda x: x['return'], reverse=True)
        
        response = {
            'period': period,
            'count': len(results[:limit]),
            'top_performers': results[:limit]
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error getting top stocks: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/client/<int:client_id>/upload', methods=['POST'])
def upload_file(client_id):
    """
    Upload a document for a client.
    
    Request: multipart/form-data with 'file' field
    Returns: File metadata and upload status
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed',
                'allowed_types': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Read file data
        file_data = file.read()
        
        # Check file size
        if len(file_data) > MAX_FILE_SIZE:
            return jsonify({
                'error': 'File too large',
                'max_size_mb': MAX_FILE_SIZE / (1024 * 1024)
            }), 400
        
        # Save file
        metadata = doc_processor.save_file(client_id, file_data, file.filename)
        
        logger.info(f"File uploaded for client {client_id}: {file.filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'File uploaded successfully',
            'file': metadata
        })
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/client/<int:client_id>/files')
def get_client_files(client_id):
    """
    Get all uploaded files for a client.
    
    Returns: List of file metadata
    """
    try:
        files = doc_processor.get_client_files(client_id)
        summary = doc_processor.get_client_summary(client_id)
        
        return jsonify({
            'client_id': client_id,
            'summary': summary,
            'files': files
        })
    
    except Exception as e:
        logger.error(f"Error getting client files: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/client/<int:client_id>/analyze/<filename>')
def analyze_file(client_id, filename):
    """
    Analyze a specific uploaded file.
    
    Returns: Analysis results
    """
    try:
        analysis = doc_processor.analyze_file(client_id, filename)
        
        return jsonify({
            'client_id': client_id,
            'filename': filename,
            'analysis': analysis
        })
    
    except Exception as e:
        logger.error(f"Error analyzing file: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/client/<int:client_id>/report', methods=['POST'])
def generate_report(client_id):
    """
    Generate comprehensive report for a client.
    
    Returns: Report metadata and download links
    """
    try:
        # Get portfolio data
        portfolio_data = db.get_portfolio_data(client_id)
        
        # Get documents summary
        documents_summary = doc_processor.get_client_summary(client_id)
        
        # Generate report
        report = report_generator.generate_client_report(
            client_id,
            portfolio_data,
            documents_summary
        )
        
        logger.info(f"Report generated for client {client_id}: {report['report_id']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Report generated successfully',
            'report': report
        })
    
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/client/<int:client_id>/reports')
def get_client_reports(client_id):
    """
    Get all reports for a client.
    
    Returns: List of reports
    """
    try:
        reports = report_generator.get_client_reports(client_id)
        
        return jsonify({
            'client_id': client_id,
            'count': len(reports),
            'reports': reports
        })
    
    except Exception as e:
        logger.error(f"Error getting reports: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/<path:filename>')
def download_report(filename):
    """
    Download a generated report.
    
    Returns: Report file
    """
    try:
        report_path = Path('data/client_reports')
        file_path = report_path / filename
        
        if not file_path.exists():
            return jsonify({'error': 'Report not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error downloading report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """
    Run backtesting on trading strategies.
    
    Request body:
    {
        "tickers": ["AAPL", "MSFT"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
        "strategy": "ml" | "buy_hold" | "compare"
    }
    
    Returns: Backtest results with performance metrics
    """
    try:
        data = request.get_json()
        
        # Validate input
        tickers = data.get('tickers', ['AAPL', 'MSFT', 'GOOGL', 'AMZN'])
        start_date = data.get('start_date', '2024-01-01')
        end_date = data.get('end_date', '2024-12-31')
        initial_capital = data.get('initial_capital', 100000)
        strategy = data.get('strategy', 'compare')
        
        # Initialize backtester
        backtester = Backtester(initial_capital=initial_capital)
        
        # Run requested strategy
        if strategy == 'ml':
            results = backtester.run_ml_strategy(tickers, start_date, end_date)
        elif strategy == 'buy_hold':
            results = backtester.run_buy_hold_strategy(tickers, start_date, end_date)
        elif strategy == 'compare':
            results = backtester.compare_strategies(tickers, start_date, end_date)
        else:
            return jsonify({'error': 'Invalid strategy. Use: ml, buy_hold, or compare'}), 400
        
        return jsonify(results)
    
    except Exception as e:
        logger.error(f"Backtesting error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/')
def index():
    """Serve the web interface."""
    return send_from_directory(static_folder, 'index.html')


if __name__ == '__main__':
    Config.validate()
    
    # Use PORT from environment (Cloud Run) or default from config
    port = int(os.environ.get('PORT', Config.API_PORT))
    host = os.environ.get('HOST', '0.0.0.0')  # Cloud Run requires 0.0.0.0
    
    logger.info("="*60)
    logger.info("Starting Investment Platform API")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"ML Predictions: {'Enabled' if predictor else 'Disabled'}")
    logger.info("="*60)
    
    app.run(
        host=host,
        port=port,
        debug=Config.DEBUG_MODE
    )
