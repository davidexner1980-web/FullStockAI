/**
 * PortfolioManager - Comprehensive portfolio tracking and analysis
 */

class PortfolioManager {
    constructor() {
        this.portfolios = new Map();
        this.currentPortfolio = null;
        this.holdings = new Map();
        this.performanceChart = null;
        this.allocationChart = null;
        this.refreshInterval = null;
        
        this.init();
    }

    init() {
        console.log('PortfolioManager: Initializing...');
        
        this.setupEventListeners();
        this.loadPortfolios();
        this.setupCharts();
        this.startPerformanceTracking();
    }

    setupEventListeners() {
        // Portfolio creation
        const createPortfolioForm = document.getElementById('create-portfolio-form');
        if (createPortfolioForm) {
            createPortfolioForm.addEventListener('submit', (event) => {
                event.preventDefault();
                this.createPortfolio();
            });
        }

        // Portfolio selection
        const portfolioSelect = document.getElementById('portfolio-select');
        if (portfolioSelect) {
            portfolioSelect.addEventListener('change', (event) => {
                this.switchPortfolio(event.target.value);
            });
        }

        // Add holding form
        const addHoldingForm = document.getElementById('add-holding-form');
        if (addHoldingForm) {
            addHoldingForm.addEventListener('submit', (event) => {
                event.preventDefault();
                this.addHolding();
            });
        }

        // Portfolio analysis
        const analyzeBtn = document.getElementById('analyze-portfolio');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                this.analyzePortfolio();
            });
        }

        // Rebalance portfolio
        const rebalanceBtn = document.getElementById('rebalance-portfolio');
        if (rebalanceBtn) {
            rebalanceBtn.addEventListener('click', () => {
                this.showRebalanceModal();
            });
        }

        // Export portfolio
        const exportBtn = document.getElementById('export-portfolio');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportPortfolio();
            });
        }

        // Performance period selector
        const periodSelector = document.getElementById('performance-period');
        if (periodSelector) {
            periodSelector.addEventListener('change', (event) => {
                this.updatePerformanceChart(event.target.value);
            });
        }

        // Remove holding buttons
        document.addEventListener('click', (event) => {
            if (event.target.closest('.remove-holding')) {
                const holdingId = event.target.closest('.remove-holding').dataset.holdingId;
                this.removeHolding(holdingId);
            }
        });

        // Edit holding buttons
        document.addEventListener('click', (event) => {
            if (event.target.closest('.edit-holding')) {
                const holdingId = event.target.closest('.edit-holding').dataset.holdingId;
                this.editHolding(holdingId);
            }
        });

        // Refresh data
        const refreshBtn = document.getElementById('refresh-portfolio');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }
    }

    async loadPortfolios() {
        this.showLoadingState();
        
        try {
            // Load user's portfolios from backend
            const response = await fetch('/api/portfolio/list');
            if (response.ok) {
                const portfolios = await response.json();
                this.processPortfolios(portfolios);
            } else {
                // Create default portfolio if none exist
                await this.createDefaultPortfolio();
            }
            
            await this.loadCurrentPortfolioData();
            this.renderPortfolioOverview();
            
        } catch (error) {
            console.error('Failed to load portfolios:', error);
            this.showErrorState('Failed to load portfolio data');
        } finally {
            this.hideLoadingState();
        }
    }

    async createDefaultPortfolio() {
        const defaultPortfolio = {
            id: 'default',
            name: 'My Portfolio',
            created_at: new Date().toISOString(),
            holdings: []
        };
        
        this.portfolios.set('default', defaultPortfolio);
        this.currentPortfolio = 'default';
        this.updatePortfolioSelector();
    }

    processPortfolios(portfolios) {
        portfolios.forEach(portfolio => {
            this.portfolios.set(portfolio.id, portfolio);
        });
        
        // Set current portfolio to first one or create default
        if (portfolios.length > 0) {
            this.currentPortfolio = portfolios[0].id;
        } else {
            this.createDefaultPortfolio();
        }
        
        this.updatePortfolioSelector();
    }

    updatePortfolioSelector() {
        const selector = document.getElementById('portfolio-select');
        if (!selector) return;

        const portfoliosArray = Array.from(this.portfolios.values());
        
        selector.innerHTML = portfoliosArray.map(portfolio => `
            <option value="${portfolio.id}" ${portfolio.id === this.currentPortfolio ? 'selected' : ''}>
                ${portfolio.name}
            </option>
        `).join('');
    }

    async loadCurrentPortfolioData() {
        if (!this.currentPortfolio) return;

        try {
            // Load holdings for current portfolio
            const response = await fetch(`/api/portfolio/${this.currentPortfolio}/holdings`);
            if (response.ok) {
                const holdings = await response.json();
                this.processHoldings(holdings);
            }
            
            // Load performance data
            const perfResponse = await fetch(`/api/portfolio/${this.currentPortfolio}/performance`);
            if (perfResponse.ok) {
                const performance = await perfResponse.json();
                this.processPerformanceData(performance);
            }
            
        } catch (error) {
            console.error('Failed to load portfolio data:', error);
        }
    }

    processHoldings(holdings) {
        this.holdings.clear();
        holdings.forEach(holding => {
            this.holdings.set(holding.id, holding);
        });
        
        this.renderHoldingsList();
        this.updateAllocationChart();
    }

    renderPortfolioOverview() {
        const overviewContainer = document.getElementById('portfolio-overview');
        if (!overviewContainer) return;

        const totalValue = this.calculateTotalValue();
        const totalGainLoss = this.calculateTotalGainLoss();
        const totalGainLossPercent = this.calculateTotalGainLossPercent();
        const holdingsCount = this.holdings.size;

        const gainLossClass = totalGainLoss >= 0 ? 'text-success' : 'text-danger';
        const gainLossIcon = totalGainLoss >= 0 ? 'trending-up' : 'trending-down';

        overviewContainer.innerHTML = `
            <div class="row g-3">
                <div class="col-6 col-md-3">
                    <div class="portfolio-metric-card">
                        <div class="metric-icon">
                            <i data-feather="dollar-sign"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">Total Value</div>
                            <div class="metric-value">$${totalValue.toFixed(2)}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="portfolio-metric-card">
                        <div class="metric-icon ${gainLossClass}">
                            <i data-feather="${gainLossIcon}"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">Total P&L</div>
                            <div class="metric-value ${gainLossClass}">
                                ${totalGainLoss >= 0 ? '+' : ''}$${totalGainLoss.toFixed(2)}
                            </div>
                            <div class="metric-secondary ${gainLossClass}">
                                ${totalGainLossPercent >= 0 ? '+' : ''}${totalGainLossPercent.toFixed(2)}%
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="portfolio-metric-card">
                        <div class="metric-icon">
                            <i data-feather="pie-chart"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">Holdings</div>
                            <div class="metric-value">${holdingsCount}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="portfolio-metric-card">
                        <div class="metric-icon">
                            <i data-feather="activity"></i>
                        </div>
                        <div class="metric-content">
                            <div class="metric-label">Diversification</div>
                            <div class="metric-value">${this.calculateDiversificationScore()}%</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    renderHoldingsList() {
        const holdingsContainer = document.getElementById('holdings-list');
        if (!holdingsContainer) return;

        if (this.holdings.size === 0) {
            holdingsContainer.innerHTML = `
                <div class="empty-state text-center py-5">
                    <i data-feather="briefcase" class="text-muted mb-3" style="width: 48px; height: 48px;"></i>
                    <h5 class="text-muted">No Holdings</h5>
                    <p class="text-muted">Add your first holding to get started</p>
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addHoldingModal">
                        <i data-feather="plus"></i> Add Holding
                    </button>
                </div>
            `;
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
            return;
        }

        const holdingsArray = Array.from(this.holdings.values());
        const holdingsHtml = holdingsArray.map(holding => this.renderHoldingCard(holding)).join('');

        holdingsContainer.innerHTML = `
            <div class="holdings-grid">
                ${holdingsHtml}
            </div>
        `;

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    renderHoldingCard(holding) {
        const currentValue = holding.quantity * holding.current_price;
        const costBasis = holding.quantity * holding.avg_price;
        const gainLoss = currentValue - costBasis;
        const gainLossPercent = (gainLoss / costBasis) * 100;
        const weight = (currentValue / this.calculateTotalValue()) * 100;

        const gainLossClass = gainLoss >= 0 ? 'text-success' : 'text-danger';
        const gainLossIcon = gainLoss >= 0 ? 'trending-up' : 'trending-down';

        return `
            <div class="holding-card" data-holding-id="${holding.id}">
                <div class="holding-header">
                    <div class="holding-info">
                        <h6 class="holding-symbol">${holding.ticker}</h6>
                        <span class="holding-type badge bg-secondary">${holding.asset_type}</span>
                    </div>
                    <div class="holding-actions">
                        <button class="btn btn-sm btn-outline-primary edit-holding" data-holding-id="${holding.id}">
                            <i data-feather="edit-2"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger remove-holding" data-holding-id="${holding.id}">
                            <i data-feather="trash-2"></i>
                        </button>
                    </div>
                </div>
                
                <div class="holding-metrics">
                    <div class="row">
                        <div class="col-6">
                            <div class="metric">
                                <label>Quantity</label>
                                <div class="value">${holding.quantity}</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="metric">
                                <label>Avg Price</label>
                                <div class="value">$${holding.avg_price.toFixed(2)}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-2">
                        <div class="col-6">
                            <div class="metric">
                                <label>Current Price</label>
                                <div class="value">$${holding.current_price.toFixed(2)}</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="metric">
                                <label>Current Value</label>
                                <div class="value">$${currentValue.toFixed(2)}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-2">
                        <div class="col-6">
                            <div class="metric">
                                <label>P&L</label>
                                <div class="value ${gainLossClass}">
                                    <i data-feather="${gainLossIcon}"></i>
                                    ${gainLoss >= 0 ? '+' : ''}$${gainLoss.toFixed(2)}
                                </div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="metric">
                                <label>P&L %</label>
                                <div class="value ${gainLossClass}">
                                    ${gainLossPercent >= 0 ? '+' : ''}${gainLossPercent.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="weight-section mt-3">
                        <label>Portfolio Weight: ${weight.toFixed(1)}%</label>
                        <div class="progress">
                            <div class="progress-bar" style="width: ${weight}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async createPortfolio() {
        const nameInput = document.getElementById('portfolio-name');
        const name = nameInput.value.trim();
        
        if (!name) {
            if (window.app) {
                window.app.showErrorMessage('Please enter a portfolio name');
            }
            return;
        }

        try {
            const response = await fetch('/api/portfolio/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: name })
            });

            if (response.ok) {
                const portfolio = await response.json();
                this.portfolios.set(portfolio.id, portfolio);
                this.currentPortfolio = portfolio.id;
                this.updatePortfolioSelector();
                
                nameInput.value = '';
                
                if (window.app) {
                    window.app.showSuccessMessage('Portfolio created successfully');
                }
                
                // Close modal if it exists
                const modal = bootstrap.Modal.getInstance(document.getElementById('createPortfolioModal'));
                if (modal) {
                    modal.hide();
                }
                
            } else {
                throw new Error('Failed to create portfolio');
            }
            
        } catch (error) {
            console.error('Portfolio creation failed:', error);
            if (window.app) {
                window.app.showErrorMessage('Failed to create portfolio', error.message);
            }
        }
    }

    switchPortfolio(portfolioId) {
        this.currentPortfolio = portfolioId;
        this.loadCurrentPortfolioData();
    }

    async addHolding() {
        const tickerInput = document.getElementById('holding-ticker');
        const quantityInput = document.getElementById('holding-quantity');
        const priceInput = document.getElementById('holding-price');
        const typeSelect = document.getElementById('holding-type');
        
        const ticker = tickerInput.value.trim().toUpperCase();
        const quantity = parseFloat(quantityInput.value);
        const price = parseFloat(priceInput.value);
        const assetType = typeSelect.value;
        
        if (!ticker || !quantity || !price) {
            if (window.app) {
                window.app.showErrorMessage('Please fill in all fields');
            }
            return;
        }

        try {
            const response = await fetch('/api/portfolio/holdings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    portfolio_id: this.currentPortfolio,
                    ticker: ticker,
                    quantity: quantity,
                    avg_price: price,
                    asset_type: assetType
                })
            });

            if (response.ok) {
                const holding = await response.json();
                
                // Get current price
                const currentPrice = await this.getCurrentPrice(ticker, assetType);
                holding.current_price = currentPrice;
                
                this.holdings.set(holding.id, holding);
                
                // Clear form
                tickerInput.value = '';
                quantityInput.value = '';
                priceInput.value = '';
                
                this.renderHoldingsList();
                this.renderPortfolioOverview();
                this.updateAllocationChart();
                
                if (window.app) {
                    window.app.showSuccessMessage(`${ticker} added to portfolio`);
                }
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addHoldingModal'));
                if (modal) {
                    modal.hide();
                }
                
            } else {
                throw new Error('Failed to add holding');
            }
            
        } catch (error) {
            console.error('Add holding failed:', error);
            if (window.app) {
                window.app.showErrorMessage('Failed to add holding', error.message);
            }
        }
    }

    async getCurrentPrice(ticker, assetType) {
        try {
            const endpoint = assetType === 'crypto' ? 
                `/api/crypto/predict/${ticker}` : 
                `/api/predict/${ticker}`;
                
            const response = await fetch(endpoint);
            if (response.ok) {
                const data = await response.json();
                return data.current_price || 0;
            }
        } catch (error) {
            console.error(`Failed to get current price for ${ticker}:`, error);
        }
        return 0;
    }

    async removeHolding(holdingId) {
        if (!confirm('Are you sure you want to remove this holding?')) {
            return;
        }

        try {
            const response = await fetch(`/api/portfolio/holdings/${holdingId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.holdings.delete(holdingId);
                this.renderHoldingsList();
                this.renderPortfolioOverview();
                this.updateAllocationChart();
                
                if (window.app) {
                    window.app.showSuccessMessage('Holding removed successfully');
                }
            } else {
                throw new Error('Failed to remove holding');
            }
            
        } catch (error) {
            console.error('Remove holding failed:', error);
            if (window.app) {
                window.app.showErrorMessage('Failed to remove holding', error.message);
            }
        }
    }

    editHolding(holdingId) {
        const holding = this.holdings.get(holdingId);
        if (!holding) return;

        // Populate edit modal with current values
        document.getElementById('edit-holding-ticker').value = holding.ticker;
        document.getElementById('edit-holding-quantity').value = holding.quantity;
        document.getElementById('edit-holding-price').value = holding.avg_price;
        document.getElementById('edit-holding-type').value = holding.asset_type;
        
        // Store holding ID for update
        document.getElementById('edit-holding-form').dataset.holdingId = holdingId;
        
        // Show edit modal
        const modal = new bootstrap.Modal(document.getElementById('editHoldingModal'));
        modal.show();
    }

    async analyzePortfolio() {
        if (this.holdings.size === 0) {
            if (window.app) {
                window.app.showErrorMessage('Add holdings to analyze portfolio');
            }
            return;
        }

        const analyzeBtn = document.getElementById('analyze-portfolio');
        if (analyzeBtn) {
            analyzeBtn.innerHTML = '<i data-feather="loader"></i> Analyzing...';
            analyzeBtn.disabled = true;
        }

        try {
            const tickers = Array.from(this.holdings.values()).map(h => h.ticker);
            const weights = Array.from(this.holdings.values()).map(h => {
                const value = h.quantity * h.current_price;
                return value / this.calculateTotalValue();
            });

            const response = await fetch('/api/portfolio/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tickers: tickers,
                    weights: weights
                })
            });

            if (response.ok) {
                const analysis = await response.json();
                this.displayAnalysisResults(analysis);
            } else {
                throw new Error('Analysis failed');
            }
            
        } catch (error) {
            console.error('Portfolio analysis failed:', error);
            if (window.app) {
                window.app.showErrorMessage('Portfolio analysis failed', error.message);
            }
        } finally {
            if (analyzeBtn) {
                analyzeBtn.innerHTML = '<i data-feather="bar-chart-2"></i> Analyze Portfolio';
                analyzeBtn.disabled = false;
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            }
        }
    }

    displayAnalysisResults(analysis) {
        const modalHtml = `
            <div class="modal fade" id="analysisResultsModal" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Portfolio Analysis Results</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${this.renderAnalysisContent(analysis)}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="portfolioManager.exportAnalysis()">
                                Export Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal
        const existingModal = document.getElementById('analysisResultsModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('analysisResultsModal'));
        modal.show();

        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    renderAnalysisContent(analysis) {
        const metrics = analysis.portfolio_metrics;
        const recommendations = analysis.recommendations;
        const stockMetrics = analysis.stock_metrics;

        return `
            <div class="analysis-results">
                <div class="row mb-4">
                    <div class="col-md-6">
                        <div class="analysis-card">
                            <h6>Portfolio Metrics</h6>
                            <div class="metrics-grid">
                                <div class="metric-item">
                                    <span class="metric-label">Annual Return</span>
                                    <span class="metric-value ${metrics.annual_return >= 0 ? 'text-success' : 'text-danger'}">
                                        ${metrics.annual_return}%
                                    </span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Volatility</span>
                                    <span class="metric-value">${metrics.annual_volatility}%</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Sharpe Ratio</span>
                                    <span class="metric-value">${metrics.sharpe_ratio}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Max Drawdown</span>
                                    <span class="metric-value text-danger">${metrics.max_drawdown}%</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Value at Risk</span>
                                    <span class="metric-value text-warning">${metrics.value_at_risk_95}%</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Avg Correlation</span>
                                    <span class="metric-value">${metrics.avg_correlation}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="analysis-card">
                            <h6>Recommendations</h6>
                            <div class="recommendations-list">
                                ${recommendations.map(rec => `
                                    <div class="recommendation-item">
                                        <i data-feather="chevron-right" class="text-primary"></i>
                                        <span>${rec}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-12">
                        <div class="analysis-card">
                            <h6>Individual Stock Analysis</h6>
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Symbol</th>
                                            <th>Weight</th>
                                            <th>Annual Return</th>
                                            <th>Volatility</th>
                                            <th>Beta</th>
                                            <th>Current Price</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${stockMetrics.map(stock => `
                                            <tr>
                                                <td><strong>${stock.ticker}</strong></td>
                                                <td>${stock.weight.toFixed(1)}%</td>
                                                <td class="${stock.annual_return >= 0 ? 'text-success' : 'text-danger'}">
                                                    ${stock.annual_return.toFixed(2)}%
                                                </td>
                                                <td>${stock.annual_volatility.toFixed(2)}%</td>
                                                <td>${stock.beta}</td>
                                                <td>$${stock.current_price.toFixed(2)}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    setupCharts() {
        this.setupPerformanceChart();
        this.setupAllocationChart();
    }

    setupPerformanceChart() {
        const canvas = document.getElementById('performance-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: 'rgb(13, 110, 253)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    setupAllocationChart() {
        const canvas = document.getElementById('allocation-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        this.allocationChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgb(255, 99, 132)',
                        'rgb(54, 162, 235)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(153, 102, 255)',
                        'rgb(255, 159, 64)',
                        'rgb(199, 199, 199)',
                        'rgb(83, 102, 255)',
                        'rgb(255, 99, 255)',
                        'rgb(99, 255, 132)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return context.label + ': ' + percentage + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    updateAllocationChart() {
        if (!this.allocationChart) return;

        const holdings = Array.from(this.holdings.values());
        const totalValue = this.calculateTotalValue();

        if (totalValue === 0) {
            this.allocationChart.data.labels = [];
            this.allocationChart.data.datasets[0].data = [];
        } else {
            this.allocationChart.data.labels = holdings.map(h => h.ticker);
            this.allocationChart.data.datasets[0].data = holdings.map(h => 
                h.quantity * h.current_price
            );
        }

        this.allocationChart.update();
    }

    updatePerformanceChart(period = '1M') {
        if (!this.performanceChart) return;

        // Mock performance data - in real app, this would come from backend
        const days = period === '1W' ? 7 : period === '1M' ? 30 : period === '3M' ? 90 : 365;
        const labels = [];
        const data = [];
        const currentValue = this.calculateTotalValue();

        for (let i = days; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString());
            
            // Simulate historical values with some volatility
            const volatility = Math.random() * 0.1 - 0.05; // ±5%
            const value = currentValue * (1 + volatility * (i / days));
            data.push(value);
        }

        this.performanceChart.data.labels = labels;
        this.performanceChart.data.datasets[0].data = data;
        this.performanceChart.update();
    }

    startPerformanceTracking() {
        // Update portfolio performance every 5 minutes
        this.refreshInterval = setInterval(() => {
            if (document.visibilityState === 'visible' && navigator.onLine) {
                this.refreshCurrentPrices();
            }
        }, 300000); // 5 minutes
    }

    async refreshCurrentPrices() {
        const holdings = Array.from(this.holdings.values());
        
        for (const holding of holdings) {
            try {
                const currentPrice = await this.getCurrentPrice(holding.ticker, holding.asset_type);
                holding.current_price = currentPrice;
            } catch (error) {
                console.warn(`Failed to update price for ${holding.ticker}:`, error);
            }
        }
        
        this.renderHoldingsList();
        this.renderPortfolioOverview();
        this.updateAllocationChart();
    }

    async refreshData() {
        const refreshBtn = document.getElementById('refresh-portfolio');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i data-feather="loader"></i> Refreshing...';
            refreshBtn.disabled = true;
        }

        try {
            await this.refreshCurrentPrices();
            
            if (window.app) {
                window.app.showSuccessMessage('Portfolio data refreshed');
            }
        } catch (error) {
            console.error('Refresh failed:', error);
            if (window.app) {
                window.app.showErrorMessage('Failed to refresh data', error.message);
            }
        } finally {
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i data-feather="refresh-cw"></i> Refresh';
                refreshBtn.disabled = false;
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }
            }
        }
    }

    exportPortfolio() {
        const portfolio = this.portfolios.get(this.currentPortfolio);
        const holdings = Array.from(this.holdings.values());
        
        const exportData = {
            portfolio: portfolio,
            holdings: holdings,
            summary: {
                total_value: this.calculateTotalValue(),
                total_gain_loss: this.calculateTotalGainLoss(),
                total_gain_loss_percent: this.calculateTotalGainLossPercent(),
                holdings_count: holdings.length,
                export_date: new Date().toISOString()
            }
        };

        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `portfolio_${portfolio.name}_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
    }

    // Calculation methods
    calculateTotalValue() {
        return Array.from(this.holdings.values()).reduce((total, holding) => {
            return total + (holding.quantity * holding.current_price);
        }, 0);
    }

    calculateTotalGainLoss() {
        return Array.from(this.holdings.values()).reduce((total, holding) => {
            const currentValue = holding.quantity * holding.current_price;
            const costBasis = holding.quantity * holding.avg_price;
            return total + (currentValue - costBasis);
        }, 0);
    }

    calculateTotalGainLossPercent() {
        const totalCostBasis = Array.from(this.holdings.values()).reduce((total, holding) => {
            return total + (holding.quantity * holding.avg_price);
        }, 0);
        
        if (totalCostBasis === 0) return 0;
        
        return (this.calculateTotalGainLoss() / totalCostBasis) * 100;
    }

    calculateDiversificationScore() {
        if (this.holdings.size === 0) return 0;
        
        const totalValue = this.calculateTotalValue();
        if (totalValue === 0) return 0;
        
        // Calculate Herfindahl-Hirschman Index for diversification
        let hhi = 0;
        this.holdings.forEach(holding => {
            const weight = (holding.quantity * holding.current_price) / totalValue;
            hhi += weight * weight;
        });
        
        // Convert to diversification score (0-100, higher is more diversified)
        return Math.round((1 - hhi) * 100);
    }

    // Utility methods
    showLoadingState() {
        const containers = ['portfolio-overview', 'holdings-list'];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = `
                    <div class="loading-state text-center py-5">
                        <div class="spinner-border text-primary mb-3"></div>
                        <p class="text-muted">Loading portfolio data...</p>
                    </div>
                `;
            }
        });
    }

    hideLoadingState() {
        // Loading states will be replaced by actual content
    }

    showErrorState(message) {
        const containers = ['portfolio-overview', 'holdings-list'];
        containers.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.innerHTML = `
                    <div class="error-state text-center py-5">
                        <i data-feather="alert-circle" class="text-danger mb-3" style="width: 48px; height: 48px;"></i>
                        <h5 class="text-danger">Error Loading Data</h5>
                        <p class="text-muted">${message}</p>
                        <button class="btn btn-primary" onclick="portfolioManager.refreshData()">
                            <i data-feather="refresh-cw"></i> Try Again
                        </button>
                    </div>
                `;
            }
        });
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        if (this.performanceChart) {
            this.performanceChart.destroy();
        }
        
        if (this.allocationChart) {
            this.allocationChart.destroy();
        }
    }
}

// Initialize portfolio manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/portfolio') {
        window.portfolioManager = new PortfolioManager();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PortfolioManager;
}
