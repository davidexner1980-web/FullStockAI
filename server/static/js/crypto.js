// FullStock AI vNext Ultimate - Cryptocurrency Module
// Enhanced crypto trading features with real-time data

class CryptoManager {
  constructor() {
    this.supportedCryptos = [];
    this.activeCrypto = null;
    this.cryptoChart = null;
    this.updateInterval = null;
    this.priceAlerts = new Map();
    
    this.init();
  }
  
  async init() {
    try {
      await this.loadSupportedCryptos();
      this.setupCryptoInterface();
      this.setupRealTimeUpdates();
      this.setupCryptoCharts();
      this.setupPriceAlerts();
      this.setupCryptoNews();
      this.loadCryptoPreferences();
      
      console.log('Crypto manager initialized');
    } catch (error) {
      console.error('Failed to initialize crypto manager:', error);
    }
  }
  
  async loadSupportedCryptos() {
    try {
      const response = await fetch('/api/crypto/list');
      if (response.ok) {
        this.supportedCryptos = await response.json();
        this.populateCryptoList();
      } else {
        throw new Error('Failed to load crypto list');
      }
    } catch (error) {
      console.error('Error loading crypto list:', error);
      // Fallback to static list
      this.supportedCryptos = [
        { symbol: 'BTC', name: 'Bitcoin', yahoo_symbol: 'BTC-USD' },
        { symbol: 'ETH', name: 'Ethereum', yahoo_symbol: 'ETH-USD' },
        { symbol: 'BNB', name: 'Binance Coin', yahoo_symbol: 'BNB-USD' },
        { symbol: 'XRP', name: 'XRP', yahoo_symbol: 'XRP-USD' },
        { symbol: 'ADA', name: 'Cardano', yahoo_symbol: 'ADA-USD' },
        { symbol: 'DOGE', name: 'Dogecoin', yahoo_symbol: 'DOGE-USD' },
        { symbol: 'MATIC', name: 'Polygon', yahoo_symbol: 'MATIC-USD' },
        { symbol: 'SOL', name: 'Solana', yahoo_symbol: 'SOL-USD' }
      ];
      this.populateCryptoList();
    }
  }
  
  populateCryptoList() {
    const cryptoGrid = document.getElementById('cryptoGrid');
    const cryptoSelect = document.getElementById('cryptoSelect');
    
    if (cryptoGrid) {
      cryptoGrid.innerHTML = this.supportedCryptos.map(crypto => `
        <div class="crypto-card" data-symbol="${crypto.symbol}" onclick="cryptoManager.selectCrypto('${crypto.symbol}')">
          <div class="crypto-header">
            <div class="crypto-icon">
              <i class="fab fa-${crypto.symbol.toLowerCase()}"></i>
            </div>
            <div class="crypto-info">
              <div class="crypto-symbol">${crypto.symbol}</div>
              <div class="crypto-name">${crypto.name}</div>
            </div>
          </div>
          <div class="crypto-price" id="price-${crypto.symbol}">
            <div class="loading">Loading...</div>
          </div>
          <div class="crypto-change" id="change-${crypto.symbol}">
            <span class="change-value">-</span>
            <span class="change-percent">-</span>
          </div>
        </div>
      `).join('');
      
      // Load initial prices
      this.loadCryptoPrices();
    }
    
    if (cryptoSelect) {
      cryptoSelect.innerHTML = '<option value="">Select Cryptocurrency</option>' +
        this.supportedCryptos.map(crypto => 
          `<option value="${crypto.symbol}">${crypto.symbol} - ${crypto.name}</option>`
        ).join('');
    }
  }
  
  async loadCryptoPrices() {
    for (const crypto of this.supportedCryptos) {
      try {
        const response = await fetch(`/api/crypto/predict/${crypto.symbol}`);
        if (response.ok) {
          const data = await response.json();
          this.updateCryptoPriceDisplay(crypto.symbol, data);
        }
      } catch (error) {
        console.error(`Failed to load price for ${crypto.symbol}:`, error);
      }
    }
  }
  
  updateCryptoPriceDisplay(symbol, data) {
    const priceElement = document.getElementById(`price-${symbol}`);
    const changeElement = document.getElementById(`change-${symbol}`);
    
    if (priceElement && data.current_price !== undefined) {
      priceElement.innerHTML = `
        <div class="current-price">$${this.formatPrice(data.current_price)}</div>
      `;
    }
    
    if (changeElement && data.predictions?.ensemble) {
      const ensemble = data.predictions.ensemble;
      const change = ensemble.price_change || 0;
      const changePercent = ensemble.price_change_percent || 0;
      const isPositive = change >= 0;
      
      changeElement.innerHTML = `
        <span class="change-value ${isPositive ? 'positive' : 'negative'}">
          ${isPositive ? '+' : ''}$${Math.abs(change).toFixed(2)}
        </span>
        <span class="change-percent ${isPositive ? 'positive' : 'negative'}">
          (${isPositive ? '+' : ''}${changePercent.toFixed(2)}%)
        </span>
      `;
      
      changeElement.className = `crypto-change ${isPositive ? 'positive' : 'negative'}`;
    }
  }
  
  async selectCrypto(symbol) {
    if (this.activeCrypto === symbol) return;
    
    this.activeCrypto = symbol;
    this.highlightActiveCrypto(symbol);
    
    try {
      // Show loading state
      this.showCryptoLoading();
      
      // Fetch detailed crypto data
      const response = await fetch(`/api/crypto/predict/${symbol}`);
      if (!response.ok) {
        throw new Error('Failed to fetch crypto data');
      }
      
      const data = await response.json();
      
      // Update displays
      this.updateCryptoAnalysis(data);
      this.updateCryptoChart(data);
      this.updateCryptoPredictions(data);
      this.updateCryptoRiskAnalysis(data);
      
      // Update URL
      this.updateURL(symbol);
      
    } catch (error) {
      console.error('Error selecting crypto:', error);
      app.showError('Failed to load cryptocurrency data');
    }
  }
  
  highlightActiveCrypto(symbol) {
    // Remove previous active state
    document.querySelectorAll('.crypto-card.active').forEach(card => {
      card.classList.remove('active');
    });
    
    // Add active state to selected crypto
    const activeCard = document.querySelector(`[data-symbol="${symbol}"]`);
    if (activeCard) {
      activeCard.classList.add('active');
    }
  }
  
  showCryptoLoading() {
    const containers = ['cryptoAnalysis', 'cryptoChart', 'cryptoPredictions', 'cryptoRiskAnalysis'];
    containers.forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        element.innerHTML = '<div class="loading-container"><div class="spinner"></div><span>Loading crypto data...</span></div>';
      }
    });
  }
  
  updateCryptoAnalysis(data) {
    const container = document.getElementById('cryptoAnalysis');
    if (!container) return;
    
    const crypto = this.supportedCryptos.find(c => c.symbol === data.symbol);
    const ensemble = data.predictions?.ensemble;
    
    if (!crypto || !ensemble) {
      container.innerHTML = '<div class="error">Analysis data unavailable</div>';
      return;
    }
    
    const isPositive = ensemble.price_change >= 0;
    
    container.innerHTML = `
      <div class="crypto-analysis-header">
        <div class="crypto-title">
          <i class="fab fa-${crypto.symbol.toLowerCase()}"></i>
          <h2>${crypto.name} (${crypto.symbol})</h2>
        </div>
        <div class="crypto-price-large">
          $${this.formatPrice(data.current_price)}
        </div>
      </div>
      
      <div class="crypto-prediction-summary">
        <div class="prediction-card ${isPositive ? 'positive' : 'negative'}">
          <div class="prediction-label">ML Ensemble Prediction</div>
          <div class="prediction-price">$${this.formatPrice(ensemble.prediction)}</div>
          <div class="prediction-change">
            <span class="change-amount">${isPositive ? '+' : ''}$${Math.abs(ensemble.price_change).toFixed(2)}</span>
            <span class="change-percent">(${ensemble.price_change_percent.toFixed(2)}%)</span>
          </div>
          <div class="prediction-confidence">
            <div class="confidence-bar">
              <div class="confidence-fill" style="width: ${ensemble.confidence * 100}%"></div>
            </div>
            <span class="confidence-text">${(ensemble.confidence * 100).toFixed(1)}% Confidence</span>
          </div>
        </div>
      </div>
      
      <div class="crypto-metrics">
        <div class="metric-item">
          <div class="metric-label">Volatility Analysis</div>
          <div class="metric-value">${data.volatility_analysis?.volatility_regime || 'N/A'}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">Market Sentiment</div>
          <div class="metric-value">${this.formatSentiment(data.market_sentiment)}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">Risk Level</div>
          <div class="metric-value ${this.getRiskClass(data.risk_analysis?.risk_level)}">${data.risk_analysis?.risk_level || 'N/A'}</div>
        </div>
      </div>
    `;
  }
  
  updateCryptoChart(data) {
    // This would integrate with the main chart system
    // For now, show placeholder
    const container = document.getElementById('cryptoChart');
    if (!container) return;
    
    container.innerHTML = `
      <div class="chart-container">
        <canvas id="cryptoPriceChart"></canvas>
      </div>
    `;
    
    // Initialize chart with crypto data
    this.initializeCryptoChart(data);
  }
  
  initializeCryptoChart(data) {
    const canvas = document.getElementById('cryptoPriceChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (this.cryptoChart) {
      this.cryptoChart.destroy();
    }
    
    // Mock data for demonstration - in real implementation, this would come from the API
    const labels = Array.from({length: 30}, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      return date.toLocaleDateString();
    });
    
    const prices = Array.from({length: 30}, (_, i) => {
      const basePrice = data.current_price;
      const variation = basePrice * 0.1 * (Math.random() - 0.5);
      return basePrice + variation;
    });
    
    this.cryptoChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: `${data.symbol} Price`,
          data: prices,
          borderColor: '#f7931a', // Bitcoin orange
          backgroundColor: 'rgba(247, 147, 26, 0.1)',
          borderWidth: 2,
          fill: true,
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
                return '$' + value.toFixed(2);
              }
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Price: $${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        }
      }
    });
  }
  
  updateCryptoPredictions(data) {
    const container = document.getElementById('cryptoPredictions');
    if (!container || !data.predictions) return;
    
    const models = ['random_forest', 'lstm', 'xgboost'];
    let html = '<div class="model-predictions">';
    
    models.forEach(modelName => {
      const model = data.predictions[modelName];
      if (model && model.prediction !== undefined) {
        const change = model.prediction - data.current_price;
        const changePercent = (change / data.current_price) * 100;
        const isPositive = change >= 0;
        
        html += `
          <div class="model-prediction-card">
            <div class="model-name">${this.formatModelName(modelName)}</div>
            <div class="model-price ${isPositive ? 'positive' : 'negative'}">
              $${this.formatPrice(model.prediction)}
            </div>
            <div class="model-change ${isPositive ? 'positive' : 'negative'}">
              ${isPositive ? '+' : ''}${changePercent.toFixed(2)}%
            </div>
            <div class="model-confidence">
              ${(model.confidence * 100).toFixed(1)}% confidence
            </div>
          </div>
        `;
      }
    });
    
    html += '</div>';
    
    // Add price targets if available
    if (data.price_targets) {
      html += this.renderPriceTargets(data.price_targets);
    }
    
    container.innerHTML = html;
  }
  
  renderPriceTargets(targets) {
    if (!targets.conservative && !targets.aggressive) return '';
    
    let html = '<div class="price-targets">';
    html += '<h3>Price Targets</h3>';
    
    if (targets.conservative) {
      html += `
        <div class="target-group">
          <h4>Conservative Targets</h4>
          <div class="target-range">
            <div class="target-item">
              <span class="target-label">Upper:</span>
              <span class="target-value positive">$${this.formatPrice(targets.conservative.upper)}</span>
              <span class="target-percent positive">(+${targets.conservative.upside.toFixed(1)}%)</span>
            </div>
            <div class="target-item">
              <span class="target-label">Lower:</span>
              <span class="target-value negative">$${this.formatPrice(targets.conservative.lower)}</span>
              <span class="target-percent negative">(${targets.conservative.downside.toFixed(1)}%)</span>
            </div>
          </div>
        </div>
      `;
    }
    
    if (targets.aggressive) {
      html += `
        <div class="target-group">
          <h4>Aggressive Targets</h4>
          <div class="target-range">
            <div class="target-item">
              <span class="target-label">Upper:</span>
              <span class="target-value positive">$${this.formatPrice(targets.aggressive.upper)}</span>
              <span class="target-percent positive">(+${targets.aggressive.upside.toFixed(1)}%)</span>
            </div>
            <div class="target-item">
              <span class="target-label">Lower:</span>
              <span class="target-value negative">$${this.formatPrice(targets.aggressive.lower)}</span>
              <span class="target-percent negative">(${targets.aggressive.downside.toFixed(1)}%)</span>
            </div>
          </div>
        </div>
      `;
    }
    
    html += '</div>';
    return html;
  }
  
  updateCryptoRiskAnalysis(data) {
    const container = document.getElementById('cryptoRiskAnalysis');
    if (!container || !data.risk_analysis) return;
    
    const risk = data.risk_analysis;
    
    container.innerHTML = `
      <div class="risk-analysis">
        <h3>Risk Analysis</h3>
        
        <div class="risk-overview">
          <div class="risk-score ${this.getRiskClass(risk.risk_level)}">
            <div class="risk-score-value">${risk.total_risk_score.toFixed(0)}</div>
            <div class="risk-score-label">Risk Score</div>
          </div>
          <div class="risk-level">
            <div class="risk-level-badge ${this.getRiskClass(risk.risk_level)}">${risk.risk_level} RISK</div>
          </div>
        </div>
        
        <div class="risk-metrics">
          <div class="risk-metric">
            <div class="risk-metric-label">Value at Risk (95%)</div>
            <div class="risk-metric-value">${risk.value_at_risk_95?.toFixed(2)}%</div>
          </div>
          <div class="risk-metric">
            <div class="risk-metric-label">Liquidity Ratio</div>
            <div class="risk-metric-value">${risk.liquidity_ratio?.toFixed(2)}</div>
          </div>
          <div class="risk-metric">
            <div class="risk-metric-label">Market Cap Risk</div>
            <div class="risk-metric-value">${risk.market_cap_risk}</div>
          </div>
        </div>
        
        ${risk.risk_factors?.length ? `
          <div class="risk-factors">
            <h4>Risk Factors</h4>
            <ul>
              ${risk.risk_factors.map(factor => `<li>${factor}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
    `;
  }
  
  setupRealTimeUpdates() {
    // Update prices every 30 seconds
    this.updateInterval = setInterval(() => {
      this.loadCryptoPrices();
      if (this.activeCrypto) {
        this.refreshActiveCrypto();
      }
    }, 30000);
  }
  
  async refreshActiveCrypto() {
    if (!this.activeCrypto) return;
    
    try {
      const response = await fetch(`/api/crypto/predict/${this.activeCrypto}`);
      if (response.ok) {
        const data = await response.json();
        this.updateCryptoAnalysis(data);
        this.updateCryptoPriceDisplay(this.activeCrypto, data);
      }
    } catch (error) {
      console.error('Failed to refresh active crypto:', error);
    }
  }
  
  setupCryptoCharts() {
    // Chart configurations are handled in individual chart methods
    console.log('Crypto charts setup complete');
  }
  
  setupPriceAlerts() {
    const alertForm = document.getElementById('cryptoAlertForm');
    if (alertForm) {
      alertForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.createPriceAlert();
      });
    }
    
    this.loadExistingAlerts();
  }
  
  async createPriceAlert() {
    const symbol = document.getElementById('alertSymbol')?.value;
    const type = document.getElementById('alertType')?.value;
    const targetPrice = parseFloat(document.getElementById('alertPrice')?.value);
    
    if (!symbol || !type || !targetPrice) {
      app.showError('Please fill in all alert fields');
      return;
    }
    
    try {
      const response = await fetch('/api/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ticker: symbol,
          alert_type: type,
          target_value: targetPrice,
          user_id: 'anonymous' // In a real app, this would be the actual user ID
        })
      });
      
      if (response.ok) {
        app.showSuccess('Price alert created successfully');
        this.loadExistingAlerts();
        this.clearAlertForm();
      } else {
        throw new Error('Failed to create alert');
      }
    } catch (error) {
      console.error('Error creating price alert:', error);
      app.showError('Failed to create price alert');
    }
  }
  
  async loadExistingAlerts() {
    try {
      const response = await fetch('/api/alerts?user_id=anonymous');
      if (response.ok) {
        const data = await response.json();
        this.displayAlerts(data.alerts || {});
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  }
  
  displayAlerts(alerts) {
    const container = document.getElementById('cryptoAlerts');
    if (!container) return;
    
    const alertList = Object.values(alerts).filter(alert => 
      this.supportedCryptos.some(crypto => crypto.symbol === alert.ticker)
    );
    
    if (alertList.length === 0) {
      container.innerHTML = '<div class="no-alerts">No price alerts set</div>';
      return;
    }
    
    container.innerHTML = alertList.map(alert => `
      <div class="alert-item ${alert.is_active ? 'active' : 'inactive'}">
        <div class="alert-symbol">${alert.ticker}</div>
        <div class="alert-condition">
          ${alert.alert_type.replace('_', ' ').toUpperCase()} $${this.formatPrice(alert.target_value)}
        </div>
        <div class="alert-status">
          ${alert.is_active ? 'Active' : 'Triggered'}
        </div>
        <button class="btn btn-sm btn-danger" onclick="cryptoManager.deleteAlert('${alert.id}')">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    `).join('');
  }
  
  async deleteAlert(alertId) {
    try {
      const response = await fetch(`/api/alerts?alert_id=${alertId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        app.showSuccess('Alert deleted successfully');
        this.loadExistingAlerts();
      } else {
        throw new Error('Failed to delete alert');
      }
    } catch (error) {
      console.error('Error deleting alert:', error);
      app.showError('Failed to delete alert');
    }
  }
  
  clearAlertForm() {
    const form = document.getElementById('cryptoAlertForm');
    if (form) {
      form.reset();
    }
  }
  
  setupCryptoNews() {
    // Placeholder for crypto news integration
    this.loadCryptoNews();
  }
  
  loadCryptoNews() {
    const newsContainer = document.getElementById('cryptoNews');
    if (!newsContainer) return;
    
    // In a real implementation, this would fetch actual crypto news
    newsContainer.innerHTML = `
      <div class="news-placeholder">
        <i class="fas fa-newspaper"></i>
        <p>Crypto news integration coming soon</p>
      </div>
    `;
  }
  
  loadCryptoPreferences() {
    const preferences = JSON.parse(localStorage.getItem('cryptoPreferences') || '{}');
    
    // Apply preferences
    if (preferences.defaultCrypto && this.supportedCryptos.some(c => c.symbol === preferences.defaultCrypto)) {
      this.selectCrypto(preferences.defaultCrypto);
    } else if (this.supportedCryptos.length > 0) {
      this.selectCrypto(this.supportedCryptos[0].symbol); // Default to first crypto
    }
  }
  
  saveCryptoPreferences() {
    const preferences = {
      defaultCrypto: this.activeCrypto,
      lastUpdated: Date.now()
    };
    localStorage.setItem('cryptoPreferences', JSON.stringify(preferences));
  }
  
  // Utility methods
  formatPrice(price) {
    if (price < 0.01) {
      return price.toFixed(6);
    } else if (price < 1) {
      return price.toFixed(4);
    } else if (price < 100) {
      return price.toFixed(2);
    } else {
      return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
  }
  
  formatModelName(modelName) {
    const names = {
      'random_forest': 'Random Forest',
      'lstm': 'LSTM Neural Net',
      'xgboost': 'XGBoost'
    };
    return names[modelName] || modelName;
  }
  
  formatSentiment(sentiment) {
    if (!sentiment) return 'N/A';
    
    if (typeof sentiment === 'object') {
      return sentiment.fear_greed_index?.classification || 'Neutral';
    }
    
    return typeof sentiment === 'string' ? sentiment : 'Neutral';
  }
  
  getRiskClass(riskLevel) {
    const level = (riskLevel || '').toLowerCase();
    switch (level) {
      case 'low': return 'risk-low';
      case 'medium': return 'risk-medium';
      case 'high': return 'risk-high';
      default: return 'risk-unknown';
    }
  }
  
  updateURL(symbol) {
    const url = new URL(window.location);
    url.searchParams.set('crypto', symbol);
    window.history.replaceState({}, '', url);
  }
  
  // Public methods for external access
  getCryptoList() {
    return this.supportedCryptos;
  }
  
  getActiveCrypto() {
    return this.activeCrypto;
  }
  
  // Cleanup
  destroy() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }
    
    if (this.cryptoChart) {
      this.cryptoChart.destroy();
    }
    
    this.saveCryptoPreferences();
  }
}

// Initialize crypto manager when page loads
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname === '/crypto' || document.getElementById('cryptoGrid')) {
    window.cryptoManager = new CryptoManager();
  }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  if (window.cryptoManager) {
    window.cryptoManager.destroy();
  }
});
