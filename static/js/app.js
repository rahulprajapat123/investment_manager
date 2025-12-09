// API Configuration
const API_BASE_URL = 'http://localhost:8080';

// State
let currentClient = 1;
let currentAction = 'BUY';
let currentPeriod = '1d';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeEventListeners();
    initializeDocumentUpload();
    checkAPIStatus();
    loadPortfolio(currentClient);
});

// Tab Navigation
function initializeTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            // Update active states
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(targetTab).classList.add('active');

            // Load content for the selected tab
            handleTabSwitch(targetTab);
        });
    });
}

// Event Listeners
function initializeEventListeners() {
    // Client selector (unified in header)
    document.getElementById('clientSelect').addEventListener('change', (e) => {
        currentClient = e.target.value;
        currentDocumentsClient = e.target.value; // Keep documents in sync
        updateClientName();
        loadPortfolio(currentClient);
        // If documents view is open, reload it
        if (document.getElementById('documents').style.display !== 'none') {
            loadClientDocuments(currentClient);
        }
    });

    // Header upload button - opens documents view
    document.getElementById('headerUploadBtn').addEventListener('click', () => {
        showDocumentsView();
    });

    // View documents button from portfolio
    document.getElementById('viewDocumentsBtn').addEventListener('click', () => {
        showDocumentsView();
    });

    // Close documents button
    document.getElementById('closeDocumentsBtn').addEventListener('click', () => {
        hideDocumentsView();
    });

    // Predict button
    document.getElementById('predictBtn').addEventListener('click', () => {
        const ticker = document.getElementById('tickerInput').value.trim().toUpperCase();
        if (ticker) {
            predictStock(ticker);
        }
    });

    // Allow Enter key for prediction
    document.getElementById('tickerInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('predictBtn').click();
        }
    });

    // Action buttons
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.action-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentAction = btn.dataset.action;
            loadRecommendations(currentAction);
        });
    });

    // Period buttons
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPeriod = btn.dataset.period;
            loadMarketOverview(currentPeriod);
        });
    });
}

// Handle tab switching
function handleTabSwitch(tab) {
    switch (tab) {
        case 'portfolio':
            loadPortfolio(currentClient);
            break;
        case 'predictions':
            // Predictions loaded on demand
            break;
        case 'recommendations':
            loadRecommendations(currentAction);
            break;
        case 'market':
            loadMarketOverview(currentPeriod);
            break;
    }
}

// Check API Status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        const statusEl = document.getElementById('apiStatus');
        const footerStatusEl = document.getElementById('footerStatus');

        if (data.status === 'healthy') {
            statusEl.innerHTML = '<span class="status-indicator"></span><span>Connected</span>';
            statusEl.classList.add('connected');
            footerStatusEl.textContent = 'Connected';
        } else {
            throw new Error('API unhealthy');
        }
    } catch (error) {
        const statusEl = document.getElementById('apiStatus');
        const footerStatusEl = document.getElementById('footerStatus');
        
        statusEl.innerHTML = '<span class="status-indicator"></span><span>Disconnected</span>';
        statusEl.classList.add('error');
        footerStatusEl.textContent = 'Disconnected';
        
        console.error('API connection failed:', error);
    }
}

// Load Portfolio
async function loadPortfolio(clientId) {
    try {
        // Update client name display
        updateClientName();
        
        const response = await fetch(`${API_BASE_URL}/api/portfolio/${clientId}`);
        const data = await response.json();

        // Update stats - API returns formatted strings
        document.getElementById('totalValue').textContent = data.total_value;
        document.getElementById('totalCost').textContent = data.total_cost;
        document.getElementById('gainLoss').textContent = data.total_gain_loss;
        document.getElementById('gainLossPercent').textContent = data.total_gain_loss_pct;
        
        // Apply color classes
        const colorClass = data.total_gain_loss.includes('-') ? 'negative' : 'positive';
        document.getElementById('gainLoss').className = `stat-value ${colorClass}`;
        document.getElementById('gainLossPercent').className = `stat-percent ${colorClass}`;
        
        const holdings = data.positions || [];
        document.getElementById('positionCount').textContent = holdings.length;

        // Update holdings table
        const tbody = document.getElementById('holdingsBody');
        tbody.innerHTML = '';

        if (holdings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">No holdings found</td></tr>';
            return;
        }

        holdings.forEach(holding => {
            const row = document.createElement('tr');
            const returnClass = holding.gain_loss.includes('-') ? 'negative' : 'positive';
            
            row.innerHTML = `
                <td><strong>${holding.ticker}</strong></td>
                <td>${holding.shares.toLocaleString()}</td>
                <td>${holding.cost_basis}</td>
                <td>${holding.current_price}</td>
                <td>${holding.position_value}</td>
                <td class="${returnClass}">${holding.gain_loss}</td>
                <td class="${returnClass}">${holding.gain_loss_pct}</td>
            `;
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('Failed to load portfolio:', error);
        document.getElementById('holdingsBody').innerHTML = 
            '<tr><td colspan="7" class="loading" style="color: #ef4444;">Failed to load portfolio data</td></tr>';
    }
}

// Predict Stock
async function predictStock(ticker) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/predict/${ticker}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();

        // Show result card
        const resultCard = document.getElementById('predictionResult');
        resultCard.style.display = 'block';

        // Update header
        document.getElementById('predTicker').textContent = ticker;
        
        const directionEl = document.getElementById('predDirection');
        directionEl.textContent = data.prediction.direction;
        directionEl.className = `prediction-badge ${data.prediction.direction.toLowerCase()}`;

        // Update details - API returns formatted strings
        document.getElementById('predPrice').textContent = formatCurrency(data.current_price);
        document.getElementById('predProbUp').textContent = data.prediction.probability_up;
        document.getElementById('predProbDown').textContent = data.prediction.probability_down;

        // Update recommendation
        const recBox = document.getElementById('recBox');
        const action = data.recommendation.action;
        recBox.className = `recommendation-box ${action.toLowerCase()}`;
        
        document.getElementById('recAction').textContent = action;
        document.getElementById('recStrength').textContent = data.recommendation.strength;
        document.getElementById('recConfidence').textContent = data.recommendation.confidence;

        // Update features (if available)
        if (data.key_features) {
            document.getElementById('feat30d').textContent = (data.key_features.return_30d * 100).toFixed(2) + '%';
            document.getElementById('featVol').textContent = data.key_features.volatility_30d.toFixed(4);
            document.getElementById('featRSI').textContent = data.key_features.rsi.toFixed(2);
            document.getElementById('featSent').textContent = data.key_features.sentiment_mean.toFixed(3);
        }

    } catch (error) {
        console.error('Failed to predict stock:', error);
        alert(`Failed to get prediction for ${ticker}. Please check if the ticker is valid.`);
    }
}

// Load Recommendations
async function loadRecommendations(action) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/recommendations?action=${action}`);
        const data = await response.json();

        const grid = document.getElementById('recommendationsGrid');
        grid.innerHTML = '';

        if (!data.recommendations || data.recommendations.length === 0) {
            grid.innerHTML = `<div class="loading">No ${action} recommendations found</div>`;
            return;
        }

        data.recommendations.forEach(rec => {
            const card = document.createElement('div');
            card.className = 'rec-card';
            
            card.innerHTML = `
                <div class="rec-card-header">
                    <div class="rec-ticker">${rec.ticker}</div>
                    <div class="rec-badge ${rec.action.toLowerCase()}">${rec.action}</div>
                </div>
                <div class="rec-details">
                    <div>
                        <span>Direction:</span>
                        <span>${rec.prediction}</span>
                    </div>
                    <div>
                        <span>Price:</span>
                        <span>${formatCurrency(rec.current_price)}</span>
                    </div>
                    <div>
                        <span>Confidence:</span>
                        <span>${rec.confidence}</span>
                    </div>
                    <div>
                        <span>Strength:</span>
                        <span>${rec.strength}</span>
                    </div>
                </div>
            `;
            
            grid.appendChild(card);
        });

    } catch (error) {
        console.error('Failed to load recommendations:', error);
        document.getElementById('recommendationsGrid').innerHTML = 
            '<div class="loading" style="color: #ef4444;">Failed to load recommendations</div>';
    }
}

// Load Market Overview
async function loadMarketOverview(period) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/top-stocks?limit=10`);
        const data = await response.json();

        const performersList = document.getElementById('performersList');
        performersList.innerHTML = '';

        if (!data.top_performers || data.top_performers.length === 0) {
            performersList.innerHTML = '<div class="loading">No market data available</div>';
            return;
        }

        data.top_performers.forEach((stock, index) => {
            const item = document.createElement('div');
            item.className = 'performer-item';
            
            const changeClass = stock.return < 0 ? 'negative' : 'positive';
            
            item.innerHTML = `
                <div class="performer-info">
                    <div class="performer-rank">${index + 1}</div>
                    <div>
                        <div class="performer-ticker">${stock.ticker}</div>
                        <div class="performer-price">${formatCurrency(stock.current_price)}</div>
                    </div>
                </div>
                <div class="performer-change">
                    <div class="performer-percent ${changeClass}">${stock.return_formatted}</div>
                </div>
            `;
            
            performersList.appendChild(item);
        });

    } catch (error) {
        console.error('Failed to load market overview:', error);
        document.getElementById('performersList').innerHTML = 
            '<div class="loading" style="color: #ef4444;">Failed to load market data</div>';
    }
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercent(value) {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

// Client name update function
function updateClientName() {
    const clientName = `Client ${currentClient}`;
    document.getElementById('currentClientName').textContent = clientName;
    document.getElementById('documentsClientName').textContent = clientName;
}

// Show/hide documents view
function showDocumentsView() {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    // Remove active from all tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    // Show documents
    const documentsDiv = document.getElementById('documents');
    documentsDiv.style.display = 'block';
    documentsDiv.classList.add('active');
    
    // Load documents for current client
    loadClientDocuments(currentClient);
}

function hideDocumentsView() {
    // Hide documents
    const documentsDiv = document.getElementById('documents');
    documentsDiv.style.display = 'none';
    documentsDiv.classList.remove('active');
    
    // Show portfolio tab
    document.querySelector('.tab[data-tab="portfolio"]').classList.add('active');
    document.getElementById('portfolio').classList.add('active');
}

// Document Upload Functions
let currentDocumentsClient = 1;

function initializeDocumentUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const generateReportBtn = document.getElementById('generateReportBtn');
    
    // Browse button
    browseBtn.addEventListener('click', () => fileInput.click());
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
    
    // Generate report button
    generateReportBtn.addEventListener('click', () => {
        generateClientReport(currentClient);
    });
}

async function uploadFile(file) {
    const progressDiv = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const uploadStatus = document.getElementById('uploadStatus');
    
    // Show progress
    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    uploadStatus.textContent = `Uploading ${file.name}...`;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        progressFill.style.width = '50%';
        
        const response = await fetch(`${API_BASE_URL}/api/client/${currentClient}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            progressFill.style.width = '100%';
            uploadStatus.textContent = '✓ Upload successful!';
            uploadStatus.style.color = '#10b981';
            
            // Reload documents list
            setTimeout(() => {
                progressDiv.style.display = 'none';
                document.getElementById('fileInput').value = '';
                loadClientDocuments(currentClient);
            }, 1500);
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        progressFill.style.width = '0%';
        uploadStatus.textContent = `✗ Upload failed: ${error.message}`;
        uploadStatus.style.color = '#ef4444';
    }
}

async function loadClientDocuments(clientId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/${clientId}/files`);
        const data = await response.json();
        
        // Update summary
        const summary = data.summary;
        document.getElementById('totalFiles').textContent = summary.total_files;
        document.getElementById('totalSize').textContent = summary.total_size_mb?.toFixed(2) + ' MB' || '0 MB';
        document.getElementById('lastUpload').textContent = summary.latest_upload || 'Never';
        
        // Update files table
        const tbody = document.getElementById('filesTableBody');
        tbody.innerHTML = '';
        
        if (summary.total_files === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No documents uploaded yet</td></tr>';
            return;
        }
        
        summary.files.forEach(file => {
            const row = document.createElement('tr');
            const sizeKB = (file.size / 1024).toFixed(2);
            
            row.innerHTML = `
                <td><strong>${file.filename}</strong></td>
                <td><span style="padding: 4px 8px; background: #f0f9ff; color: #0369a1; border-radius: 4px; font-size: 12px;">${file.type}</span></td>
                <td>${sizeKB} KB</td>
                <td>${formatDate(file.date)}</td>
                <td>
                    <button class="analyze-btn" onclick="analyzeDocument('${file.filename}')">Analyze</button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        // Load reports
        loadClientReports(clientId);
        
    } catch (error) {
        console.error('Failed to load documents:', error);
        document.getElementById('filesTableBody').innerHTML = 
            '<tr><td colspan="5" class="loading" style="color: #ef4444;">Failed to load documents</td></tr>';
    }
}

async function analyzeDocument(filename) {
    const modal = document.getElementById('analysisModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    modalTitle.textContent = `Analyzing: ${filename}`;
    modalBody.innerHTML = '<div class="loading">Analyzing document...</div>';
    modal.style.display = 'flex';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/${currentDocumentsClient}/analyze/${encodeURIComponent(filename)}`);
        const data = await response.json();
        
        if (data.analysis && data.analysis.data) {
            const analysisData = data.analysis.data;
            let htmlContent = '<div style="padding: 20px;">';
            
            // Display analysis based on type
            if (analysisData.rows !== undefined) {
                // CSV/Excel data
                htmlContent += `
                    <h3>Data Overview</h3>
                    <p><strong>Rows:</strong> ${analysisData.rows}</p>
                    <p><strong>Columns:</strong> ${analysisData.columns}</p>
                    <p><strong>Column Names:</strong> ${analysisData.column_names?.join(', ')}</p>
                `;
                
                if (analysisData.numeric_summary && Object.keys(analysisData.numeric_summary).length > 0) {
                    htmlContent += '<h3>Numeric Analysis</h3><table style="width: 100%; border-collapse: collapse; margin: 10px 0;"><tr><th>Column</th><th>Mean</th><th>Min</th><th>Max</th></tr>';
                    for (const [col, stats] of Object.entries(analysisData.numeric_summary)) {
                        htmlContent += `<tr><td>${col}</td><td>${stats.mean?.toFixed(2)}</td><td>${stats.min?.toFixed(2)}</td><td>${stats.max?.toFixed(2)}</td></tr>`;
                    }
                    htmlContent += '</table>';
                }
            }
            
            if (analysisData.page_count !== undefined) {
                // PDF data
                htmlContent += `
                    <h3>PDF Information</h3>
                    <p><strong>Pages:</strong> ${analysisData.page_count}</p>
                    <p><strong>Text Length:</strong> ${analysisData.text_length} characters</p>
                `;
                
                if (analysisData.financial_keywords && Object.keys(analysisData.financial_keywords).length > 0) {
                    htmlContent += '<h3>Financial Keywords Found</h3><ul>';
                    for (const [keyword, count] of Object.entries(analysisData.financial_keywords)) {
                        htmlContent += `<li><strong>${keyword}:</strong> ${count} mentions</li>`;
                    }
                    htmlContent += '</ul>';
                }
            }
            
            htmlContent += '</div>';
            modalBody.innerHTML = htmlContent;
        } else {
            modalBody.innerHTML = '<div style="padding: 20px; color: #ef4444;">Analysis failed or no data available</div>';
        }
    } catch (error) {
        console.error('Analysis error:', error);
        modalBody.innerHTML = '<div style="padding: 20px; color: #ef4444;">Failed to analyze document</div>';
    }
}

async function generateClientReport(clientId) {
    const btn = document.getElementById('generateReportBtn');
    const originalText = btn.textContent;
    btn.textContent = 'Generating...';
    btn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/${clientId}/report`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok) {
            btn.textContent = '✓ Report Generated!';
            btn.style.background = '#10b981';
            
            // Reload reports list
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '';
                btn.disabled = false;
                loadClientReports(clientId);
                document.getElementById('reportsCard').style.display = 'block';
            }, 2000);
        } else {
            throw new Error(data.error || 'Report generation failed');
        }
    } catch (error) {
        console.error('Report generation error:', error);
        btn.textContent = '✗ Failed';
        btn.style.background = '#ef4444';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
            btn.disabled = false;
        }, 2000);
    }
}

async function loadClientReports(clientId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/client/${clientId}/reports`);
        const data = await response.json();
        
        const reportsList = document.getElementById('reportsList');
        const reportsCard = document.getElementById('reportsCard');
        
        if (data.count === 0) {
            reportsList.innerHTML = '<div class="loading">No reports generated yet</div>';
            return;
        }
        
        reportsCard.style.display = 'block';
        reportsList.innerHTML = '';
        
        data.reports.forEach(report => {
            const reportDiv = document.createElement('div');
            reportDiv.className = 'report-item';
            
            const date = new Date(report.generated_date);
            const htmlFilename = report.file_path.replace('.json', '.html').split(/[\\/]/).pop();
            
            reportDiv.innerHTML = `
                <div class="report-info">
                    <h4>${report.report_id}</h4>
                    <p>Generated: ${date.toLocaleString()}</p>
                </div>
                <div class="report-actions">
                    <button class="download-btn" onclick="downloadReport('${htmlFilename}', 'html')">View HTML</button>
                    <button class="download-btn" onclick="downloadReport('${report.file_path.split(/[\\/]/).pop()}', 'json')">Download JSON</button>
                </div>
            `;
            
            reportsList.appendChild(reportDiv);
        });
    } catch (error) {
        console.error('Failed to load reports:', error);
    }
}

function downloadReport(filename, type) {
    const url = `${API_BASE_URL}/api/report/${filename}`;
    window.open(url, '_blank');
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const year = dateStr.substring(0, 4);
    const month = dateStr.substring(4, 6);
    const day = dateStr.substring(6, 8);
    const hour = dateStr.substring(9, 11);
    const min = dateStr.substring(11, 13);
    return `${year}-${month}-${day} ${hour}:${min}`;
}

// Close modal
document.addEventListener('click', (e) => {
    const modal = document.getElementById('analysisModal');
    const modalClose = document.getElementById('modalClose');
    
    if (e.target === modal || e.target === modalClose) {
        modal.style.display = 'none';
    }
});

// Auto-refresh every 30 seconds
setInterval(() => {
    const activeTab = document.querySelector('.tab.active').dataset.tab;
    if (activeTab === 'portfolio') {
        loadPortfolio(currentClient);
    }
    checkAPIStatus();
}, 30000);
