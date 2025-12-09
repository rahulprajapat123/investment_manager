"""
Document Processor for Client Files
Handles PDF, Excel, CSV, and other financial documents
"""

import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import re

class DocumentProcessor:
    """Process and analyze client financial documents."""
    
    def __init__(self, base_path='data/client_documents'):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def get_client_folder(self, client_id):
        """Get or create folder for specific client."""
        client_folder = self.base_path / f"client_{client_id}"
        client_folder.mkdir(exist_ok=True)
        return client_folder
    
    def save_file(self, client_id, file_data, filename):
        """
        Save uploaded file for a client.
        
        Args:
            client_id: Client identifier
            file_data: Binary file data
            filename: Original filename
            
        Returns:
            dict: File metadata
        """
        client_folder = self.get_client_folder(client_id)
        
        # Generate safe filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = self._sanitize_filename(filename)
        final_filename = f"{timestamp}_{safe_filename}"
        
        file_path = client_folder / final_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        file_ext = Path(filename).suffix.lower()
        
        metadata = {
            'client_id': client_id,
            'original_filename': filename,
            'saved_filename': final_filename,
            'file_path': str(file_path),
            'file_size': file_size,
            'file_type': file_ext,
            'upload_date': timestamp,
            'processed': False
        }
        
        # Save metadata
        self._save_metadata(client_id, metadata)
        
        return metadata
    
    def _sanitize_filename(self, filename):
        """Remove unsafe characters from filename."""
        # Remove path components
        filename = os.path.basename(filename)
        # Remove unsafe characters
        filename = re.sub(r'[^\w\s.-]', '', filename)
        return filename
    
    def _save_metadata(self, client_id, metadata):
        """Save file metadata to JSON."""
        metadata_file = self.get_client_folder(client_id) / 'metadata.json'
        
        # Load existing metadata
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                all_metadata = json.load(f)
        else:
            all_metadata = []
        
        # Append new metadata
        all_metadata.append(metadata)
        
        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(all_metadata, f, indent=2)
    
    def get_client_files(self, client_id):
        """Get all files for a client."""
        metadata_file = self.get_client_folder(client_id) / 'metadata.json'
        
        if not metadata_file.exists():
            return []
        
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    def process_csv(self, file_path):
        """Process CSV file and extract financial data."""
        try:
            df = pd.read_csv(file_path)
            
            analysis = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'data_types': df.dtypes.astype(str).to_dict(),
                'sample_data': df.head(5).to_dict('records'),
                'numeric_summary': {}
            }
            
            # Analyze numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            for col in numeric_cols:
                analysis['numeric_summary'][col] = {
                    'mean': float(df[col].mean()),
                    'median': float(df[col].median()),
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'std': float(df[col].std())
                }
            
            # Look for common financial columns
            financial_indicators = self._identify_financial_data(df)
            analysis['financial_indicators'] = financial_indicators
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def process_excel(self, file_path):
        """Process Excel file and extract financial data."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                sheets_data[sheet_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist(),
                    'sample_data': df.head(3).to_dict('records'),
                    'numeric_summary': {}
                }
                
                # Analyze numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns
                for col in numeric_cols:
                    if not df[col].empty:
                        sheets_data[sheet_name]['numeric_summary'][col] = {
                            'mean': float(df[col].mean()),
                            'total': float(df[col].sum()),
                            'min': float(df[col].min()),
                            'max': float(df[col].max())
                        }
            
            return {
                'sheets': list(excel_file.sheet_names),
                'sheet_count': len(excel_file.sheet_names),
                'data': sheets_data
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def process_pdf(self, file_path):
        """Process PDF file and extract text."""
        try:
            # Try to import PyPDF2 (optional dependency)
            try:
                import PyPDF2
                
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    
                    text_content = []
                    for page in pdf_reader.pages:
                        text_content.append(page.extract_text())
                    
                    full_text = '\n'.join(text_content)
                    
                    return {
                        'page_count': len(pdf_reader.pages),
                        'text_length': len(full_text),
                        'preview': full_text[:500] if full_text else '',
                        'financial_keywords': self._extract_financial_keywords(full_text)
                    }
            except ImportError:
                # Fallback: basic file info without text extraction
                file_size = os.path.getsize(file_path)
                return {
                    'page_count': 'unknown',
                    'file_size': file_size,
                    'note': 'Install PyPDF2 for text extraction: pip install PyPDF2'
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def _identify_financial_data(self, df):
        """Identify financial data patterns in DataFrame."""
        indicators = {
            'has_dates': False,
            'has_amounts': False,
            'has_transactions': False,
            'potential_metrics': []
        }
        
        # Check for date columns
        date_keywords = ['date', 'time', 'timestamp', 'period']
        for col in df.columns:
            if any(kw in col.lower() for kw in date_keywords):
                indicators['has_dates'] = True
                break
        
        # Check for amount/value columns
        amount_keywords = ['amount', 'value', 'price', 'balance', 'total', 'revenue', 'cost']
        for col in df.columns:
            if any(kw in col.lower() for kw in amount_keywords):
                indicators['has_amounts'] = True
                indicators['potential_metrics'].append(col)
        
        # Check for transaction indicators
        transaction_keywords = ['transaction', 'trade', 'order', 'payment']
        for col in df.columns:
            if any(kw in col.lower() for kw in transaction_keywords):
                indicators['has_transactions'] = True
                break
        
        return indicators
    
    def _extract_financial_keywords(self, text):
        """Extract financial keywords from text."""
        keywords = {
            'portfolio': text.lower().count('portfolio'),
            'investment': text.lower().count('investment'),
            'stock': text.lower().count('stock'),
            'bond': text.lower().count('bond'),
            'dividend': text.lower().count('dividend'),
            'return': text.lower().count('return'),
            'risk': text.lower().count('risk'),
            'asset': text.lower().count('asset')
        }
        
        # Filter out zero counts
        return {k: v for k, v in keywords.items() if v > 0}
    
    def analyze_file(self, client_id, filename):
        """Analyze a specific client file."""
        files = self.get_client_files(client_id)
        
        # Find the file
        file_info = None
        for f in files:
            if f['saved_filename'] == filename or f['original_filename'] == filename:
                file_info = f
                break
        
        if not file_info:
            return {'error': 'File not found'}
        
        file_path = file_info['file_path']
        file_type = file_info['file_type']
        
        # Process based on file type
        analysis = {'file_info': file_info}
        
        if file_type == '.csv':
            analysis['data'] = self.process_csv(file_path)
        elif file_type in ['.xlsx', '.xls']:
            analysis['data'] = self.process_excel(file_path)
        elif file_type == '.pdf':
            analysis['data'] = self.process_pdf(file_path)
        else:
            analysis['data'] = {'note': f'File type {file_type} not yet supported'}
        
        return analysis
    
    def get_client_summary(self, client_id):
        """Get summary of all documents for a client."""
        files = self.get_client_files(client_id)
        
        summary = {
            'client_id': client_id,
            'total_files': len(files),
            'file_types': {},
            'total_size': 0,
            'latest_upload': None,
            'files': []
        }
        
        for file_info in files:
            # Count by type
            file_type = file_info['file_type']
            summary['file_types'][file_type] = summary['file_types'].get(file_type, 0) + 1
            
            # Sum sizes
            summary['total_size'] += file_info['file_size']
            
            # Track latest
            if not summary['latest_upload'] or file_info['upload_date'] > summary['latest_upload']:
                summary['latest_upload'] = file_info['upload_date']
            
            # Add to files list
            summary['files'].append({
                'filename': file_info['original_filename'],
                'size': file_info['file_size'],
                'type': file_info['file_type'],
                'date': file_info['upload_date']
            })
        
        return summary
