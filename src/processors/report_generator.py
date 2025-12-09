"""
Report Generator for Client Analysis
Creates comprehensive reports from uploaded documents and portfolio data
"""

import json
from datetime import datetime
from pathlib import Path
import pandas as pd

class ReportGenerator:
    """Generate comprehensive client reports."""
    
    def __init__(self, report_path='data/client_reports'):
        self.report_path = Path(report_path)
        self.report_path.mkdir(parents=True, exist_ok=True)
    
    def generate_client_report(self, client_id, portfolio_data, documents_summary, analysis_results=None):
        """
        Generate comprehensive client report.
        
        Args:
            client_id: Client identifier
            portfolio_data: Current portfolio information
            documents_summary: Summary of uploaded documents
            analysis_results: Optional analysis from documents
            
        Returns:
            dict: Report data and file path
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        report = {
            'report_id': f'RPT-{client_id}-{timestamp}',
            'client_id': client_id,
            'generated_date': datetime.now().isoformat(),
            'sections': {}
        }
        
        # Section 1: Executive Summary
        report['sections']['executive_summary'] = self._generate_executive_summary(
            client_id, portfolio_data, documents_summary
        )
        
        # Section 2: Portfolio Analysis
        report['sections']['portfolio_analysis'] = self._analyze_portfolio(portfolio_data)
        
        # Section 3: Document Analysis
        report['sections']['document_analysis'] = self._analyze_documents(documents_summary)
        
        # Section 4: Risk Assessment
        report['sections']['risk_assessment'] = self._assess_risk(portfolio_data)
        
        # Section 5: Recommendations
        report['sections']['recommendations'] = self._generate_recommendations(
            portfolio_data, analysis_results
        )
        
        # Save report
        report_file = self.report_path / f'client_{client_id}_report_{timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML version
        html_file = self._generate_html_report(report)
        
        return {
            'report_id': report['report_id'],
            'json_path': str(report_file),
            'html_path': str(html_file),
            'summary': report['sections']['executive_summary']
        }
    
    def _generate_executive_summary(self, client_id, portfolio_data, documents_summary):
        """Generate executive summary section."""
        summary = {
            'client_id': client_id,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'key_metrics': {}
        }
        
        if portfolio_data:
            summary['key_metrics']['portfolio_value'] = portfolio_data.get('total_value', 'N/A')
            summary['key_metrics']['gain_loss'] = portfolio_data.get('total_gain_loss', 'N/A')
            summary['key_metrics']['gain_loss_pct'] = portfolio_data.get('total_gain_loss_pct', 'N/A')
            summary['key_metrics']['positions'] = len(portfolio_data.get('positions', []))
        
        if documents_summary:
            summary['documents_uploaded'] = documents_summary.get('total_files', 0)
            summary['latest_document'] = documents_summary.get('latest_upload', 'N/A')
        
        return summary
    
    def _analyze_portfolio(self, portfolio_data):
        """Analyze portfolio composition and performance."""
        if not portfolio_data or 'positions' not in portfolio_data:
            return {'status': 'No portfolio data available'}
        
        positions = portfolio_data['positions']
        
        analysis = {
            'total_positions': len(positions),
            'holdings': [],
            'diversification': {},
            'performance': {}
        }
        
        # Analyze each position
        for pos in positions:
            analysis['holdings'].append({
                'ticker': pos['ticker'],
                'shares': pos['shares'],
                'value': pos.get('position_value', 'N/A'),
                'gain_loss': pos.get('gain_loss', 'N/A'),
                'gain_loss_pct': pos.get('gain_loss_pct', 'N/A')
            })
        
        # Calculate diversification
        analysis['diversification']['number_of_stocks'] = len(positions)
        analysis['diversification']['status'] = 'Well Diversified' if len(positions) >= 5 else 'Consider More Diversification'
        
        # Performance metrics
        if portfolio_data.get('total_gain_loss'):
            gain_loss_str = portfolio_data['total_gain_loss'].replace('$', '').replace(',', '')
            if gain_loss_str.startswith('+'):
                gain_loss_str = gain_loss_str[1:]
            elif gain_loss_str.startswith('-'):
                gain_loss_str = gain_loss_str[1:]
                gain_loss_val = -float(gain_loss_str)
            else:
                try:
                    gain_loss_val = float(gain_loss_str)
                except:
                    gain_loss_val = 0
            
            analysis['performance']['overall_return'] = portfolio_data.get('total_gain_loss_pct', 'N/A')
            analysis['performance']['status'] = 'Positive' if '+' in portfolio_data.get('total_gain_loss', '') else 'Negative'
        
        return analysis
    
    def _analyze_documents(self, documents_summary):
        """Analyze uploaded documents."""
        if not documents_summary:
            return {'status': 'No documents uploaded'}
        
        analysis = {
            'total_files': documents_summary.get('total_files', 0),
            'file_types': documents_summary.get('file_types', {}),
            'total_size_mb': round(documents_summary.get('total_size', 0) / (1024 * 1024), 2),
            'files': documents_summary.get('files', [])
        }
        
        # Insights
        insights = []
        if analysis['total_files'] > 0:
            insights.append(f"{analysis['total_files']} documents uploaded for analysis")
        if '.csv' in analysis['file_types']:
            insights.append(f"{analysis['file_types']['.csv']} CSV files with transaction data")
        if '.xlsx' in analysis['file_types'] or '.xls' in analysis['file_types']:
            excel_count = analysis['file_types'].get('.xlsx', 0) + analysis['file_types'].get('.xls', 0)
            insights.append(f"{excel_count} Excel files with financial data")
        if '.pdf' in analysis['file_types']:
            insights.append(f"{analysis['file_types']['.pdf']} PDF reports uploaded")
        
        analysis['insights'] = insights
        
        return analysis
    
    def _assess_risk(self, portfolio_data):
        """Assess portfolio risk."""
        if not portfolio_data or 'positions' not in portfolio_data:
            return {'status': 'Insufficient data for risk assessment'}
        
        positions = portfolio_data['positions']
        
        risk_assessment = {
            'concentration_risk': 'Low',
            'volatility_risk': 'Medium',
            'diversification_score': 0,
            'recommendations': []
        }
        
        # Concentration risk
        if len(positions) < 3:
            risk_assessment['concentration_risk'] = 'High'
            risk_assessment['recommendations'].append('Increase diversification to reduce concentration risk')
        elif len(positions) < 5:
            risk_assessment['concentration_risk'] = 'Medium'
        
        # Diversification score (simple: based on number of positions)
        if len(positions) >= 10:
            risk_assessment['diversification_score'] = 90
        elif len(positions) >= 5:
            risk_assessment['diversification_score'] = 70
        elif len(positions) >= 3:
            risk_assessment['diversification_score'] = 50
        else:
            risk_assessment['diversification_score'] = 30
        
        return risk_assessment
    
    def _generate_recommendations(self, portfolio_data, analysis_results):
        """Generate actionable recommendations."""
        recommendations = {
            'priority_actions': [],
            'general_advice': [],
            'next_steps': []
        }
        
        # Portfolio-based recommendations
        if portfolio_data and 'positions' in portfolio_data:
            positions = portfolio_data['positions']
            
            if len(positions) < 5:
                recommendations['priority_actions'].append({
                    'action': 'Increase Diversification',
                    'reason': f'Currently holding only {len(positions)} positions',
                    'priority': 'High'
                })
            
            # Check for losses
            losses = [p for p in positions if '-' in str(p.get('gain_loss', ''))]
            if losses:
                recommendations['priority_actions'].append({
                    'action': 'Review Underperforming Assets',
                    'reason': f'{len(losses)} positions showing losses',
                    'priority': 'Medium'
                })
        
        # General advice
        recommendations['general_advice'] = [
            'Regularly review and rebalance portfolio',
            'Consider dollar-cost averaging for new investments',
            'Monitor risk exposure across asset classes',
            'Keep emergency fund separate from investments'
        ]
        
        # Next steps
        recommendations['next_steps'] = [
            'Upload recent financial statements for deeper analysis',
            'Schedule quarterly portfolio review',
            'Consider tax-loss harvesting opportunities',
            'Review investment goals and risk tolerance'
        ]
        
        return recommendations
    
    def _generate_html_report(self, report_data):
        """Generate HTML version of the report."""
        client_id = report_data['client_id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Client Report - {client_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .header .meta {{
            opacity: 0.9;
            margin-top: 10px;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .recommendation {{
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin: 10px 0;
        }}
        .priority-high {{ border-left-color: #ef4444; background: #fef2f2; }}
        .priority-medium {{ border-left-color: #f59e0b; background: #fffbeb; }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Investment Portfolio Report</h1>
        <div class="meta">
            <p><strong>Report ID:</strong> {report_data['report_id']}</p>
            <p><strong>Client ID:</strong> {client_id}</p>
            <p><strong>Generated:</strong> {report_data['generated_date']}</p>
        </div>
    </div>
"""
        
        # Executive Summary
        exec_summary = report_data['sections'].get('executive_summary', {})
        html_content += """
    <div class="section">
        <h2>📊 Executive Summary</h2>
"""
        if exec_summary.get('key_metrics'):
            metrics = exec_summary['key_metrics']
            html_content += f"""
        <div class="metric">
            <div class="metric-label">Portfolio Value</div>
            <div class="metric-value">{metrics.get('portfolio_value', 'N/A')}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Gain/Loss</div>
            <div class="metric-value {'positive' if '+' in str(metrics.get('gain_loss', '')) else 'negative'}">
                {metrics.get('gain_loss', 'N/A')}
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">Return</div>
            <div class="metric-value {'positive' if '+' in str(metrics.get('gain_loss_pct', '')) else 'negative'}">
                {metrics.get('gain_loss_pct', 'N/A')}
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">Positions</div>
            <div class="metric-value">{metrics.get('positions', 0)}</div>
        </div>
"""
        html_content += """
    </div>
"""
        
        # Portfolio Analysis
        portfolio_analysis = report_data['sections'].get('portfolio_analysis', {})
        if portfolio_analysis.get('holdings'):
            html_content += """
    <div class="section">
        <h2>💼 Portfolio Holdings</h2>
        <table>
            <thead>
                <tr>
                    <th>Ticker</th>
                    <th>Shares</th>
                    <th>Value</th>
                    <th>Gain/Loss</th>
                    <th>Return %</th>
                </tr>
            </thead>
            <tbody>
"""
            for holding in portfolio_analysis['holdings']:
                gain_class = 'positive' if '+' in str(holding.get('gain_loss', '')) else 'negative'
                html_content += f"""
                <tr>
                    <td><strong>{holding['ticker']}</strong></td>
                    <td>{holding['shares']}</td>
                    <td>{holding['value']}</td>
                    <td class="{gain_class}">{holding['gain_loss']}</td>
                    <td class="{gain_class}">{holding['gain_loss_pct']}</td>
                </tr>
"""
            html_content += """
            </tbody>
        </table>
    </div>
"""
        
        # Document Analysis
        doc_analysis = report_data['sections'].get('document_analysis', {})
        if doc_analysis.get('total_files', 0) > 0:
            html_content += f"""
    <div class="section">
        <h2>📄 Document Analysis</h2>
        <p><strong>Total Documents:</strong> {doc_analysis['total_files']}</p>
        <p><strong>Total Size:</strong> {doc_analysis.get('total_size_mb', 0)} MB</p>
        <p><strong>File Types:</strong> {', '.join([f'{k}: {v}' for k, v in doc_analysis.get('file_types', {}).items()])}</p>
"""
            if doc_analysis.get('insights'):
                html_content += "<h3>Insights:</h3><ul>"
                for insight in doc_analysis['insights']:
                    html_content += f"<li>{insight}</li>"
                html_content += "</ul>"
            html_content += """
    </div>
"""
        
        # Recommendations
        recommendations = report_data['sections'].get('recommendations', {})
        if recommendations.get('priority_actions'):
            html_content += """
    <div class="section">
        <h2>💡 Recommendations</h2>
        <h3>Priority Actions:</h3>
"""
            for rec in recommendations['priority_actions']:
                priority_class = f"priority-{rec.get('priority', 'medium').lower()}"
                html_content += f"""
        <div class="recommendation {priority_class}">
            <strong>{rec['action']}</strong><br>
            <span style="color: #666;">{rec['reason']}</span>
            <span style="float: right; font-weight: bold;">{rec['priority']} Priority</span>
        </div>
"""
            html_content += """
    </div>
"""
        
        html_content += """
    <div class="footer">
        <p>This report is generated for informational purposes only.</p>
        <p>Consult with a financial advisor before making investment decisions.</p>
    </div>
</body>
</html>
"""
        
        # Save HTML file
        html_file = self.report_path / f'client_{client_id}_report_{timestamp}.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def get_client_reports(self, client_id):
        """Get all reports for a client."""
        reports = []
        
        for file in self.report_path.glob(f'client_{client_id}_report_*.json'):
            with open(file, 'r') as f:
                report_data = json.load(f)
                reports.append({
                    'report_id': report_data['report_id'],
                    'generated_date': report_data['generated_date'],
                    'file_path': str(file)
                })
        
        return sorted(reports, key=lambda x: x['generated_date'], reverse=True)
