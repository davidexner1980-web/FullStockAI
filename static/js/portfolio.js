// FullStock AI vNext Ultimate - Portfolio Management Module
// Advanced portfolio tracking and analysis

class PortfolioManager {
  constructor() {
    this.portfolio = {
      positions: new Map(),
      totalValue: 0,
      totalCost: 0,
      dailyPnL: 0,
      totalPnL: 0
    };
    
    this.watchlist = new Set();
    this.alerts = new Map();
    this.portfolioChart = null;
    this.allocationChart = null;
    this.performanceChart = null;
    
    this.refreshInterval = null;
    this.isLoading = false;
    
    this.init();
  }
  
  init() {
    this.loadPortfolioData();
    this.setupPortfolioInterface();
    this.setupPortfolioCharts();
    this.setupRealTimeUpdates();
    this.setupPositionManagement();
    this.setupPerformanceTracking();
    this.loadWatchlist();
    
    console.log('Portfolio manager initialized');
  }
  
  loadPortfolioData() {
    const savedPortfolio = localStorage.getItem('portfolioData');
    if (savedPortfolio) {
      try {
        const data = JSON.parse(savedPortfolio);
        if (data.positions) {
          this.portfolio.positions = new Map(Object.entries(data.positions));
        }
        if (data.totalValue) this.portfolio.totalValue = data.totalValue;
        if (data.totalCost) this.portfolio.totalCost = data.totalCost;
      } catch (error) {
        console.error('Error loading portfolio data:', error);
      }
    }
    
    this.refreshPortfolioValues();
  }
  
  savePortfolioData() {
    const data = {
      positions: Object.fromEntries(this.portfolio.positions),
      totalValue: this.portfolio.totalValue,
      totalCost: this.portfolio.totalCost,
      lastUpdated: Date.now()
    };
    localStorage.setItem('portfolioData', JSON.stringify(data));
  }
  
  setupPortfolioInterface() {
    this.setupAddPositionForm();
    this.setupPortfolioSummary();
    this.setupPositionsList();
    this.setupPortfolioAnalysis();
    this.updatePortfolioDisplay();
  }
  
  setupAddPositionForm() {
    const form = document.getElementById('addPositionForm');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.addPosition();
      });
    }
    
    // Auto-complete for ticker input
    const tickerInput = document.getElementById('positionTicker');
    if (tickerInput) {
      tickerInput.addEventListener('input', this.debounce((e) => {
        this.showTickerSuggestions(e.target.value);
      }, 300));
    }
  }
  
  async addPosition() {
    const ticker = document.getElementById('positionTicker')?.value?.toUpperCase();
    const quantity = parseFloat(document.getElementById('positionQuantity')?.value);
    const purchasePrice = parseFloat(document.getElementById('positionPrice')?.value);
    const purchaseDate = document.getElementById('positionDate')?.value;
    
    if (!ticker || !quantity || !purchasePrice) {
      app.showError('Please fill in all required fields');
      return;
    }
    
    if (this.portfolio.positions.has(ticker)) {
      // Update existing position
      const existing = this.portfolio.positions.get(ticker);
      const totalQuantity = existing.quantity + quantity;
      const totalCost = (existing.quantity * existing.averagePrice) + (quantity * purchasePrice);
      const newAveragePrice = totalCost / totalQuantity;
      
      this.portfolio.positions.set(ticker, {
        ...existing,
        quantity: totalQuantity,
        averagePrice: newAveragePrice,
        totalCost: totalCost,
        lastUpdated: Date.now()
      });
    } else {
      // Add new position
      this.portfolio.positions.set(ticker, {
        ticker,
        quantity,
        averagePrice: purchasePrice,
        purchasePrice,
        purchaseDate: purchaseDate || new Date().toISOString().split('T')[0],
        totalCost: quantity * purchasePrice,
        currentPrice: purchasePrice,
        currentValue: quantity * purchasePrice,
        pnl: 0,
        pnlPercent: 0,
        addedAt: Date.now(),
        lastUpdated: Date.now()
      });
    }
    
    // Clear form
    document.getElementById('addPositionForm')?.reset();
    
    // Update displays
    await this.refreshPortfolioValues();
    this.updatePortfolioDisplay();
    this.savePortfolioData();
    
    app.showSuccess(`Added ${quantity} shares of ${ticker} to portfolio`);
  }
  
  async removePosition(ticker) {
    if (!this.portfolio.positions.has(ticker)) return;
    
    if (confirm(`Remove ${ticker} from portfolio?`)) {
      this.portfolio.positions.delete(ticker);
      await this.refreshPortfolioValues();
      this.updatePortfolioDisplay();
      this.savePortfolioData();
      
      app.showSuccess(`${ticker} removed from portfolio`);
    }
  }
  
  async editPosition(ticker) {
    const position = this.portfolio.positions.get(ticker);
    if (!position) return;
    
    // Create edit modal
    const modal = this.createEditPositionModal(position);
    document.body.appendChild(modal);
  }
  
  createEditPositionModal(position) {
    const modal = document.createElement('div');
    modal.className = 'position-edit-modal';
    modal.innerHTML = `
      <div class="modal-overlay" onclick="this.parentElement.remove()"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Edit Position: ${position.ticker}</h3>
          <button class="btn-close" onclick="this.closest('.position-edit-modal').remove()">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <form id="editPositionForm">
            <div class="form-group">
              <label>Quantity</label>
              <input type="number" id="editQuantity" value="${position.quantity}" step="0.001" required>
            </div>
            <div class="form-group">
              <label>Average Price</label>
              <input type="number" id="editPrice" value="${position.averagePrice}" step="0.01" required>
            </div>
            <div class="form-group">
              <label>Purchase Date</label>
              <input type="date" id="editDate" value="${position.purchaseDate}">
            </div>
            <div class="form-actions">
              <button type="submit" class="btn btn-primary">Update Position</button>
              <button type="button" class="btn btn-secondary" onclick="this.closest('.position-edit-modal').remove()">Cancel</button>
            </div>
          </form>
        </div>
      </div>
    `;
    
    // Handle form submission
    const form = modal.querySelector('#editPositionForm');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this.updatePosition(position.ticker);
      modal.remove();
    });
    
    return modal;
  }
  
  async updatePosition(ticker) {
    const position = this.portfolio.positions.get(ticker);
    if (!position) return;
    
    const quantity = parseFloat(document.getElementById('editQuantity')?.value);
    const averagePrice = parseFloat(document.getElementById('editPrice')?.value);
    const purchaseDate = document.getElementById('editDate')?.value;
    
    if (!quantity || !averagePrice) {
      app.showError('Invalid position data');
      return;
    }
    
    // Update position
    this.portfolio.positions.set(ticker, {
      ...position,
      quantity,
      averagePrice,
      purchaseDate,
      totalCost: quantity * averagePrice,
      lastUpdated: Date.now()
    });
    
    await this.refreshPortfolioValues();
    this.updatePortfolioDisplay();
    this.savePortfolioData();
    
    app.showSuccess(`${ticker} position updated`);
  }
  
  async refreshPortfolioValues() {
    if (this.portfolio.positions.size === 0) {
      this.portfolio.totalValue = 0;
      this.portfolio.totalCost = 0;
      this.portfolio.totalPnL = 0;
      this.portfolio.dailyPnL = 0;
      return;
    }
    
    this.isLoading = true;
    const positions = Array.from(this.portfolio.positions.keys());
    
    try {
      // Fetch current prices for all positions
      const pricePromises = positions.map(ticker => this.fetchCurrentPrice(ticker));
      const prices = await Promise.allSettled(pricePromises);
      
      let totalValue = 0;
      let totalCost = 0;
      
      positions.forEach((ticker, index) => {
        const position = this.portfolio.positions.get(ticker);
        const priceResult = prices[index];
        
        if (priceResult.status === 'fulfilled' && priceResult.value) {
          const currentPrice = priceResult.value;
          const currentValue = position.quantity * currentPrice;
          const pnl = currentValue - position.totalCost;
          const pnlPercent = (pnl / position.totalCost) * 100;
          
          // Update position
          this.portfolio.positions.set(ticker, {
            ...position,
            currentPrice,
            currentValue,
            pnl,
            pnlPercent,
            lastUpdated: Date.now()
          });
          
          totalValue += currentValue;
          totalCost += position.totalCost;
        } else {
          // Use last known values if price fetch failed
          totalValue += position.currentValue || position.totalCost;
          totalCost += position.totalCost;
        }
      });
      
      this.portfolio.totalValue = totalValue;
      this.portfolio.totalCost = totalCost;
      this.portfolio.totalPnL = totalValue - totalCost;
      
    } catch (error) {
      console.error('Error refreshing portfolio values:', error);
    } finally {
      this.isLoading = false;
    }
  }
  
  async fetchCurrentPrice(ticker) {
    try {
      const response = await fetch(`/api/predict/${ticker}`);
      if (response.ok) {
        const data = await response.json();
        return data.current_price;
      }
    } catch (error) {
      console.error(`Error fetching price for ${ticker}:`, error);
    }
    return null;
  }
  
  updatePortfolioDisplay() {
    this.updatePortfolioSummary();
    this.updatePositionsList();
    this.updatePortfolioCharts();
  }
  
  updatePortfolioSummary() {
    const summaryContainer = document.getElementById('portfolioSummary');
    if (!summaryContainer) return;
    
    const totalPnLPercent = this.portfolio.totalCost > 0 ? 
      (this.portfolio.totalPnL / this.portfolio.totalCost) * 100 : 0;
    
    const isPositive = this.portfolio.totalPnL >= 0;
    
    summaryContainer.innerHTML = `
      <div class="portfolio-overview">
        <div class="portfolio-metric">
          <div class="metric-label">Total Value</div>
          <div class="metric-value">${this.formatCurrency(this.portfolio.totalValue)}</div>
        </div>
        <div class="portfolio-metric">
          <div class="metric-label">Total Cost</div>
          <div class="metric-value">${this.formatCurrency(this.portfolio.totalCost)}</div>
        </div>
        <div class="portfolio-metric">
          <div class="metric-label">Total P&L</div>
          <div class="metric-value ${isPositive ? 'positive' : 'negative'}">
            ${isPositive ? '+' : ''}${this.formatCurrency(this.portfolio.totalPnL)}
            <span class="metric-percent">(${totalPnLPercent.toFixed(2)}%)</span>
          </div>
        </div>
        <div class="portfolio-metric">
          <div class="metric-label">Positions</div>
          <div class="metric-value">${this.portfolio.positions.size}</div>
        </div>
      </div>
    `;
  }
  
  updatePositionsList() {
    const container = document.getElementById('positionsList');
    if (!container) return;
    
    if (this.portfolio.positions.size === 0) {
      container.innerHTML = `
        <div class="empty-portfolio">
          <i class="fas fa-briefcase"></i>
          <h3>Your portfolio is empty</h3>
          <p>Add your first position to get started</p>
        </div>
      `;
      return;
    }
    
    const positions = Array.from(this.portfolio.positions.values())
      .sort((a, b) => b.currentValue - a.currentValue);
    
    container.innerHTML = `
      <div class="positions-table">
        <div class="positions-header">
          <div class="col-ticker">Symbol</div>
          <div class="col-quantity">Shares</div>
          <div class="col-price">Avg Price</div>
          <div class="col-current">Current</div>
          <div class="col-value">Value</div>
          <div class="col-pnl">P&L</div>
          <div class="col-actions">Actions</div>
        </div>
        <div class="positions-body">
          ${positions.map(position => this.renderPositionRow(position)).join('')}
        </div>
      </div>
    `;
  }
  
  renderPositionRow(position) {
    const isPositive = position.pnl >= 0;
    const allocation = this.portfolio.totalValue > 0 ? 
      (position.currentValue / this.portfolio.totalValue) * 100 : 0;
    
    return `
      <div class="position-row" data-ticker="${position.ticker}">
        <div class="col-ticker">
          <div class="position-symbol">${position.ticker}</div>
          <div class="position-allocation">${allocation.toFixed(1)}%</div>
        </div>
        <div class="col-quantity">${position.quantity.toLocaleString()}</div>
        <div class="col-price">${this.formatCurrency(position.averagePrice)}</div>
        <div class="col-current">
          ${this.formatCurrency(position.currentPrice)}
          ${this.isLoading ? '<i class="fas fa-spinner fa-spin"></i>' : ''}
        </div>
        <div class="col-value">${this.formatCurrency(position.currentValue)}</div>
        <div class="col-pnl ${isPositive ? 'positive' : 'negative'}">
          ${isPositive ? '+' : ''}${this.formatCurrency(position.pnl)}
          <div class="pnl-percent">(${position.pnlPercent.toFixed(2)}%)</div>
        </div>
        <div class="col-actions">
          <button class="btn btn-sm btn-outline" onclick="portfolioManager.editPosition('${position.ticker}')" title="Edit">
            <i class="fas fa-edit"></i>
          </button>
          <button class="btn btn-sm btn-outline" onclick="portfolioManager.analyzePosition('${position.ticker}')" title="Analyze">
            <i class="fas fa-chart-line"></i>
          </button>
          <button class="btn btn-sm btn-danger" onclick="portfolioManager.removePosition('${position.ticker}')" title="Remove">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    `;
  }
  
  async analyzePosition(ticker) {
    // Navigate to analysis page with the ticker
    window.location.href = `/?ticker=${ticker}`;
  }
  
  setupPortfolioCharts() {
    this.initializeAllocationChart();
    this.initializePerformanceChart();
  }
  
  updatePortfolioCharts() {
    this.updateAllocationChart();
    this.updatePerformanceChart();
  }
  
  initializeAllocationChart() {
    const canvas = document.getElementById('allocationChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (this.allocationChart) {
      this.allocationChart.destroy();
    }
    
    this.allocationChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
          ],
          borderColor: 'var(--bg-primary)',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.parsed;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${percentage}% ($${value.toLocaleString()})`;
              }
            }
          }
        }
      }
    });
    
    this.updateAllocationChart();
  }
  
  updateAllocationChart() {
    if (!this.allocationChart) return;
    
    const positions = Array.from(this.portfolio.positions.values())
      .filter(p => p.currentValue > 0)
      .sort((a, b) => b.currentValue - a.currentValue);
    
    const labels = positions.map(p => p.ticker);
    const data = positions.map(p => p.currentValue);
    
    this.allocationChart.data.labels = labels;
    this.allocationChart.data.datasets[0].data = data;
    this.allocationChart.update('none');
  }
  
  initializePerformanceChart() {
    const canvas = document.getElementById('performanceChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    if (this.performanceChart) {
      this.performanceChart.destroy();
    }
    
    // Generate mock performance data
    const performanceData = this.generatePerformanceData();
    
    this.performanceChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: performanceData.labels,
        datasets: [{
          label: 'Portfolio Value',
          data: performanceData.values,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1
        }, {
          label: 'Total Cost',
          data: performanceData.costs,
          borderColor: '#6b7280',
          backgroundColor: 'transparent',
          borderWidth: 1,
          borderDash: [5, 5],
          fill: false
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
                return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
              }
            }
          }
        }
      }
    });
  }
  
  generatePerformanceData() {
    // This would typically come from historical portfolio data
    const days = 30;
    const labels = [];
    const values = [];
    const costs = [];
    
    const baseValue = this.portfolio.totalCost || 10000;
    const currentValue = this.portfolio.totalValue || baseValue;
    const dailyChange = (currentValue - baseValue) / days;
    
    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
      
      // Simulate gradual change with some randomness
      const progress = (days - i) / days;
      const noise = (Math.random() - 0.5) * baseValue * 0.02;
      values.push(baseValue + (dailyChange * (days - i)) + noise);
      costs.push(baseValue);
    }
    
    return { labels, values, costs };
  }
  
  updatePerformanceChart() {
    if (!this.performanceChart) return;
    
    const performanceData = this.generatePerformanceData();
    this.performanceChart.data.labels = performanceData.labels;
    this.performanceChart.data.datasets[0].data = performanceData.values;
    this.performanceChart.data.datasets[1].data = performanceData.costs;
    this.performanceChart.update('none');
  }
  
  setupRealTimeUpdates() {
    // Update portfolio every 2 minutes
    this.refreshInterval = setInterval(() => {
      if (!this.isLoading) {
        this.refreshPortfolioValues().then(() => {
          this.updatePortfolioDisplay();
          this.savePortfolioData();
        });
      }
    }, 120000); // 2 minutes
  }
  
  setupPositionManagement() {
    // Position management is handled through the form and button events
  }
  
  setupPerformanceTracking() {
    // Load performance history from localStorage
    this.loadPerformanceHistory();
    
    // Track daily snapshots
    this.trackDailySnapshot();
  }
  
  loadPerformanceHistory() {
    const history = localStorage.getItem('portfolioHistory');
    if (history) {
      try {
        this.performanceHistory = JSON.parse(history);
      } catch (error) {
        console.error('Error loading performance history:', error);
        this.performanceHistory = [];
      }
    } else {
      this.performanceHistory = [];
    }
  }
  
  trackDailySnapshot() {
    const today = new Date().toDateString();
    const lastSnapshot = this.performanceHistory[this.performanceHistory.length - 1];
    
    if (!lastSnapshot || new Date(lastSnapshot.date).toDateString() !== today) {
      const snapshot = {
        date: new Date().toISOString(),
        totalValue: this.portfolio.totalValue,
        totalCost: this.portfolio.totalCost,
        totalPnL: this.portfolio.totalPnL,
        positionCount: this.portfolio.positions.size,
        positions: Array.from(this.portfolio.positions.entries()).map(([ticker, position]) => ({
          ticker,
          quantity: position.quantity,
          currentPrice: position.currentPrice,
          currentValue: position.currentValue,
          pnl: position.pnl
        }))
      };
      
      this.performanceHistory.push(snapshot);
      
      // Keep only last 90 days
      if (this.performanceHistory.length > 90) {
        this.performanceHistory = this.performanceHistory.slice(-90);
      }
      
      localStorage.setItem('portfolioHistory', JSON.stringify(this.performanceHistory));
    }
  }
  
  loadWatchlist() {
    const watchlist = localStorage.getItem('portfolioWatchlist');
    if (watchlist) {
      try {
        this.watchlist = new Set(JSON.parse(watchlist));
      } catch (error) {
        console.error('Error loading watchlist:', error);
      }
    }
    
    this.updateWatchlistDisplay();
  }
  
  addToWatchlist(ticker) {
    this.watchlist.add(ticker.toUpperCase());
    localStorage.setItem('portfolioWatchlist', JSON.stringify([...this.watchlist]));
    this.updateWatchlistDisplay();
    
    app.showSuccess(`${ticker} added to watchlist`);
  }
  
  removeFromWatchlist(ticker) {
    this.watchlist.delete(ticker);
    localStorage.setItem('portfolioWatchlist', JSON.stringify([...this.watchlist]));
    this.updateWatchlistDisplay();
    
    app.showSuccess(`${ticker} removed from watchlist`);
  }
  
  updateWatchlistDisplay() {
    const container = document.getElementById('portfolioWatchlist');
    if (!container) return;
    
    if (this.watchlist.size === 0) {
      container.innerHTML = '<div class="empty-watchlist">No stocks in watchlist</div>';
      return;
    }
    
    container.innerHTML = `
      <div class="watchlist-items">
        ${Array.from(this.watchlist).map(ticker => `
          <div class="watchlist-item">
            <span class="watchlist-ticker">${ticker}</span>
            <div class="watchlist-actions">
              <button class="btn btn-sm btn-outline" onclick="portfolioManager.analyzePosition('${ticker}')" title="Analyze">
                <i class="fas fa-chart-line"></i>
              </button>
              <button class="btn btn-sm btn-outline" onclick="portfolioManager.addPositionFromWatchlist('${ticker}')" title="Add to Portfolio">
                <i class="fas fa-plus"></i>
              </button>
              <button class="btn btn-sm btn-danger" onclick="portfolioManager.removeFromWatchlist('${ticker}')" title="Remove">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }
  
  addPositionFromWatchlist(ticker) {
    // Pre-fill the add position form
    const tickerInput = document.getElementById('positionTicker');
    if (tickerInput) {
      tickerInput.value = ticker;
      tickerInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
  
  // Portfolio analysis methods
  async analyzePortfolio() {
    if (this.portfolio.positions.size === 0) {
      app.showError('Portfolio is empty. Add some positions first.');
      return;
    }
    
    const tickers = Array.from(this.portfolio.positions.keys());
    const weights = Array.from(this.portfolio.positions.values()).map(position => 
      position.currentValue / this.portfolio.totalValue
    );
    
    try {
      const response = await fetch('/api/portfolio/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tickers, weights })
      });
      
      if (response.ok) {
        const analysis = await response.json();
        this.displayPortfolioAnalysis(analysis);
      } else {
        throw new Error('Failed to analyze portfolio');
      }
    } catch (error) {
      console.error('Portfolio analysis error:', error);
      app.showError('Failed to analyze portfolio');
    }
  }
  
  displayPortfolioAnalysis(analysis) {
    const container = document.getElementById('portfolioAnalysisResults');
    if (!container) return;
    
    container.innerHTML = `
      <div class="portfolio-analysis">
        <h3>Portfolio Analysis Results</h3>
        
        <div class="analysis-metrics">
          <div class="metric-group">
            <h4>Portfolio Metrics</h4>
            <div class="metric-item">
              <span>Expected Return:</span>
              <span class="${analysis.portfolio_metrics?.expected_return >= 0 ? 'positive' : 'negative'}">
                ${(analysis.portfolio_metrics?.expected_return * 100).toFixed(2)}%
              </span>
            </div>
            <div class="metric-item">
              <span>Volatility:</span>
              <span>${(analysis.portfolio_metrics?.expected_volatility * 100).toFixed(2)}%</span>
            </div>
            <div class="metric-item">
              <span>Sharpe Ratio:</span>
              <span>${analysis.portfolio_metrics?.sharpe_ratio?.toFixed(2) || 'N/A'}</span>
            </div>
            <div class="metric-item">
              <span>Diversification Score:</span>
              <span>${analysis.diversification_score?.toFixed(1) || 'N/A'}/100</span>
            </div>
          </div>
          
          <div class="metric-group">
            <h4>Risk Analysis</h4>
            <div class="risk-level ${this.getRiskLevelClass(analysis.risk_analysis?.risk_level)}">
              ${analysis.risk_analysis?.risk_level || 'Unknown'} RISK
            </div>
            <div class="risk-score">
              Risk Score: ${analysis.risk_analysis?.overall_risk_score?.toFixed(0) || 'N/A'}/100
            </div>
          </div>
        </div>
        
        ${analysis.optimization_suggestions?.optimization_suggestions ? `
          <div class="optimization-suggestions">
            <h4>Optimization Suggestions</h4>
            <ul>
              ${analysis.optimization_suggestions.optimization_suggestions.map(suggestion => 
                `<li>${suggestion}</li>`
              ).join('')}
            </ul>
          </div>
        ` : ''}
        
        ${analysis.oracle_synthesis ? `
          <div class="oracle-portfolio-synthesis">
            <h4>Oracle Portfolio Synthesis</h4>
            <div class="oracle-state">${analysis.oracle_synthesis.oracle_state}</div>
            <div class="oracle-narrative">${analysis.oracle_synthesis.portfolio_synthesis}</div>
          </div>
        ` : ''}
      </div>
    `;
  }
  
  // Utility methods
  formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  }
  
  getRiskLevelClass(level) {
    switch ((level || '').toLowerCase()) {
      case 'low': return 'risk-low';
      case 'medium': return 'risk-medium';
      case 'high': return 'risk-high';
      default: return 'risk-unknown';
    }
  }
  
  showTickerSuggestions(query) {
    // Implementation for ticker auto-complete
    if (query.length < 1) return;
    
    // This could integrate with a ticker search API
    const commonTickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX'];
    const suggestions = commonTickers.filter(ticker => 
      ticker.toLowerCase().includes(query.toLowerCase())
    );
    
    // Show suggestions (implementation would depend on UI design)
    console.log('Ticker suggestions:', suggestions);
  }
  
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }
  
  // Export/Import functionality
  exportPortfolio() {
    const portfolioData = {
      positions: Object.fromEntries(this.portfolio.positions),
      summary: {
        totalValue: this.portfolio.totalValue,
        totalCost: this.portfolio.totalCost,
        totalPnL: this.portfolio.totalPnL
      },
      performanceHistory: this.performanceHistory,
      watchlist: Array.from(this.watchlist),
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(portfolioData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `portfolio-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
    app.showSuccess('Portfolio exported successfully');
  }
  
  importPortfolio(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        
        if (data.positions) {
          this.portfolio.positions = new Map(Object.entries(data.positions));
          this.refreshPortfolioValues();
          this.updatePortfolioDisplay();
          this.savePortfolioData();
        }
        
        if (data.watchlist) {
          this.watchlist = new Set(data.watchlist);
          this.updateWatchlistDisplay();
        }
        
        if (data.performanceHistory) {
          this.performanceHistory = data.performanceHistory;
          localStorage.setItem('portfolioHistory', JSON.stringify(this.performanceHistory));
        }
        
        app.showSuccess('Portfolio imported successfully');
      } catch (error) {
        console.error('Error importing portfolio:', error);
        app.showError('Failed to import portfolio file');
      }
    };
    
    reader.readAsText(file);
  }
  
  // Cleanup
  destroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    
    if (this.portfolioChart) {
      this.portfolioChart.destroy();
    }
    
    if (this.allocationChart) {
      this.allocationChart.destroy();
    }
    
    if (this.performanceChart) {
      this.performanceChart.destroy();
    }
    
    this.savePortfolioData();
  }
}

// Initialize portfolio manager
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname === '/portfolio' || document.getElementById('portfolioSummary')) {
    window.portfolioManager = new PortfolioManager();
  }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.portfolioManager) {
    window.portfolioManager.destroy();
  }
});
