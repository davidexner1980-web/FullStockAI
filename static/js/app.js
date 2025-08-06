// FullStock AI vNext Ultimate - Main Application JavaScript
// Enhanced mobile-first trading experience

class FullStockApp {
  constructor() {
    this.initializeApp();
    this.setupEventListeners();
    this.setupServiceWorker();
    this.initializeTheme();
    this.setupMobileFeatures();
    this.initializeNotifications();
    
    // Chart instance
    this.chart = null;
    
    // Current ticker
    this.currentTicker = '';
    
    // Cache for API responses
    this.cache = new Map();
    
    // WebSocket connection
    this.socket = null;
    
    // State management
    this.state = {
      isOracleMode: false,
      currentTheme: 'dark',
      isLoading: false,
      notifications: [],
      watchlist: [],
      isOnline: navigator.onLine
    };
    
    console.log('FullStock AI vNext Ultimate initialized');
  }
  
  initializeApp() {
    // Initialize Chart.js defaults
    if (typeof Chart !== 'undefined') {
      Chart.defaults.color = '#c9d1d9';
      Chart.defaults.borderColor = 'rgba(139, 148, 158, 0.2)';
      Chart.defaults.backgroundColor = 'rgba(59, 130, 246, 0.1)';
      Chart.defaults.plugins.legend.display = true;
      Chart.defaults.plugins.tooltip.backgroundColor = '#21262d';
      Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
      Chart.defaults.plugins.tooltip.bodyColor = '#c9d1d9';
      Chart.defaults.plugins.tooltip.borderColor = '#30363d';
      Chart.defaults.plugins.tooltip.borderWidth = 1;
      Chart.defaults.responsive = true;
      Chart.defaults.maintainAspectRatio = false;
    }
    
    // Initialize UI components
    this.initializeTooltips();
    this.initializeModals();
    this.loadUserPreferences();
    this.loadWatchlist();
    
    // Set up viewport height for mobile
    this.setViewportHeight();
  }
  
  setupEventListeners() {
    // Search functionality
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    
    if (searchForm) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const ticker = searchInput.value.trim().toUpperCase();
        if (ticker) {
          this.analyzeTicker(ticker);
        }
      });
    }
    
    // Real-time search suggestions
    if (searchInput) {
      searchInput.addEventListener('input', this.debounce((e) => {
        const query = e.target.value.trim();
        if (query.length > 0) {
          this.showSearchSuggestions(query);
        } else {
          this.hideSearchSuggestions();
        }
      }, 300));
    }
    
    // Oracle mode toggle
    const oracleToggle = document.getElementById('oracleToggle');
    if (oracleToggle) {
      oracleToggle.addEventListener('change', (e) => {
        this.state.isOracleMode = e.target.checked;
        this.updateOracleMode();
        if (this.currentTicker) {
          this.updateOracleInsights(this.currentTicker);
        }
      });
    }
    
    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        this.toggleTheme();
      });
    }
    
    // Mobile menu
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileNav = document.getElementById('mobileNav');
    const mobileNavOverlay = document.getElementById('mobileNavOverlay');
    const mobileNavClose = document.getElementById('mobileNavClose');
    
    if (mobileMenuToggle && mobileNav) {
      mobileMenuToggle.addEventListener('click', () => {
        this.toggleMobileMenu();
      });
    }
    
    if (mobileNavClose) {
      mobileNavClose.addEventListener('click', () => {
        this.closeMobileMenu();
      });
    }
    
    if (mobileNavOverlay) {
      mobileNavOverlay.addEventListener('click', () => {
        this.closeMobileMenu();
      });
    }
    
    // Floating panel toggle
    const floatingPanel = document.getElementById('floatingPanel');
    const floatingPanelToggle = document.getElementById('floatingPanelToggle');
    
    if (floatingPanelToggle && floatingPanel) {
      floatingPanelToggle.addEventListener('click', () => {
        floatingPanel.classList.toggle('collapsed');
      });
    }
    
    // Window events
    window.addEventListener('resize', this.debounce(() => {
      this.setViewportHeight();
      if (this.chart) {
        this.chart.resize();
      }
    }, 250));
    
    // Online/offline events
    window.addEventListener('online', () => {
      this.state.isOnline = true;
      this.updateConnectionStatus();
      this.syncOfflineData();
    });
    
    window.addEventListener('offline', () => {
      this.state.isOnline = false;
      this.updateConnectionStatus();
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      this.handleKeyboardShortcuts(e);
    });
    
    // Page visibility change
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && this.currentTicker) {
        this.refreshCurrentAnalysis();
      }
    });
  }
  
  setupServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/static/sw.js')
        .then((registration) => {
          console.log('Service Worker registered:', registration);
          
          // Listen for updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.showUpdateNotification();
              }
            });
          });
        })
        .catch((error) => {
          console.log('Service Worker registration failed:', error);
        });
      
      // Listen for messages from service worker
      navigator.serviceWorker.addEventListener('message', (event) => {
        this.handleServiceWorkerMessage(event.data);
      });
    }
  }
  
  initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    this.state.currentTheme = savedTheme;
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.innerHTML = savedTheme === 'dark' ? 
        '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
  }
  
  setupMobileFeatures() {
    // Touch gestures for charts and cards
    this.setupTouchGestures();
    
    // Pull to refresh
    this.setupPullToRefresh();
    
    // Swipe navigation
    this.setupSwipeNavigation();
    
    // Haptic feedback (if available)
    this.setupHapticFeedback();
    
    // iOS specific fixes
    if (this.isIOS()) {
      this.setupIOSFixes();
    }
  }
  
  initializeNotifications() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
    
    // Set up push notifications
    this.setupPushNotifications();
  }
  
  async analyzeTicker(ticker) {
    if (!ticker || this.state.isLoading) return;
    
    this.currentTicker = ticker;
    this.state.isLoading = true;
    this.updateLoadingState(true);
    
    try {
      // Show loading states
      this.showLoadingStates();
      
      // Fetch all data concurrently
      const promises = [
        this.fetchPrediction(ticker),
        this.fetchChartData(ticker),
        this.fetchTradingSignals(ticker)
      ];
      
      if (this.state.isOracleMode) {
        promises.push(this.fetchOracleInsights(ticker));
      }
      
      const results = await Promise.allSettled(promises);
      
      // Process results
      const [predictionResult, chartResult, signalsResult, oracleResult] = results;
      
      if (predictionResult.status === 'fulfilled') {
        this.updatePredictionDisplay(predictionResult.value);
      } else {
        this.showError('Failed to fetch prediction data');
      }
      
      if (chartResult.status === 'fulfilled') {
        this.updateChart(chartResult.value);
      } else {
        this.showError('Failed to fetch chart data');
      }
      
      if (signalsResult.status === 'fulfilled') {
        this.updateTradingSignals(signalsResult.value);
      } else {
        this.showError('Failed to fetch trading signals');
      }
      
      if (oracleResult && oracleResult.status === 'fulfilled') {
        this.updateOracleDisplay(oracleResult.value);
      }
      
      // Update URL and add to history
      this.updateURL(ticker);
      this.addToSearchHistory(ticker);
      
      // Send message to service worker to cache this ticker
      if (navigator.serviceWorker && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: 'CACHE_TICKER',
          payload: { ticker }
        });
      }
      
    } catch (error) {
      console.error('Error analyzing ticker:', error);
      this.showError('Analysis failed. Please try again.');
    } finally {
      this.state.isLoading = false;
      this.updateLoadingState(false);
      this.hideLoadingStates();
    }
  }
  
  async fetchPrediction(ticker) {
    const cacheKey = `prediction_${ticker}`;
    
    // Check cache first
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 minutes
        return cached.data;
      }
    }
    
    const response = await fetch(`/api/predict/${ticker}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Cache the result
    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now()
    });
    
    return data;
  }
  
  async fetchChartData(ticker) {
    const cacheKey = `chart_${ticker}`;
    
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < 5 * 60 * 1000) {
        return cached.data;
      }
    }
    
    const response = await fetch(`/api/chart_data/${ticker}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    this.cache.set(cacheKey, { data, timestamp: Date.now() });
    return data;
  }
  
  async fetchTradingSignals(ticker) {
    const cacheKey = `signals_${ticker}`;
    
    if (this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < 5 * 60 * 1000) {
        return cached.data;
      }
    }
    
    const response = await fetch(`/api/strategies/${ticker}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    this.cache.set(cacheKey, { data, timestamp: Date.now() });
    return data;
  }
  
  async fetchOracleInsights(ticker) {
    const response = await fetch(`/api/oracle/${ticker}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  }
  
  updatePredictionDisplay(data) {
    // Update main prediction cards
    this.updateModelComparison(data);
    this.updateEnsemblePrediction(data);
    this.updateConfidenceDisplay(data);
    
    // Trigger haptic feedback for significant predictions
    const ensemblePrediction = data.predictions?.ensemble;
    if (ensemblePrediction && Math.abs(ensemblePrediction.price_change_percent) > 5) {
      this.triggerHapticFeedback('medium');
    }
  }
  
  updateModelComparison(data) {
    const modelsContainer = document.getElementById('modelComparison');
    if (!modelsContainer || !data.predictions) return;
    
    const models = ['random_forest', 'lstm', 'xgboost'];
    let html = '';
    
    models.forEach(modelName => {
      const model = data.predictions[modelName];
      if (model && model.prediction !== undefined) {
        const change = model.prediction - data.current_price;
        const changePercent = (change / data.current_price) * 100;
        const isPositive = change >= 0;
        
        html += `
          <div class="model-card">
            <div class="model-name">${this.formatModelName(modelName)}</div>
            <div class="model-prediction ${isPositive ? 'text-success' : 'text-danger'}">
              $${model.prediction.toFixed(2)}
            </div>
            <div class="model-change ${isPositive ? 'text-success' : 'text-danger'}">
              ${isPositive ? '+' : ''}${changePercent.toFixed(2)}%
            </div>
            <div class="model-confidence">
              ${(model.confidence * 100).toFixed(1)}% confidence
            </div>
          </div>
        `;
      }
    });
    
    modelsContainer.innerHTML = html;
  }
  
  updateEnsemblePrediction(data) {
    const ensembleContainer = document.getElementById('ensemblePrediction');
    if (!ensembleContainer || !data.predictions?.ensemble) return;
    
    const ensemble = data.predictions.ensemble;
    const change = ensemble.prediction - data.current_price;
    const changePercent = (change / data.current_price) * 100;
    const isPositive = change >= 0;
    
    ensembleContainer.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Ensemble Prediction</h3>
          <span class="badge ${isPositive ? 'bg-success' : 'bg-danger'}">
            ${isPositive ? 'Bullish' : 'Bearish'}
          </span>
        </div>
        <div class="card-body text-center">
          <div class="prediction-value ${isPositive ? 'text-success' : 'text-danger'}">
            $${ensemble.prediction.toFixed(2)}
          </div>
          <div class="prediction-change ${isPositive ? 'text-success' : 'text-danger'}">
            ${isPositive ? '+' : ''}$${change.toFixed(2)} (${changePercent.toFixed(2)}%)
          </div>
          <div class="prediction-confidence">
            <span>Confidence: ${(ensemble.confidence * 100).toFixed(1)}%</span>
            <div class="confidence-bar">
              <div class="confidence-fill" style="width: ${ensemble.confidence * 100}%"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  
  updateChart(data) {
    const canvas = document.getElementById('priceChart');
    if (!canvas || !data.labels || !data.prices) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (this.chart) {
      this.chart.destroy();
    }
    
    // Prepare data
    const chartData = {
      labels: data.labels,
      datasets: [
        {
          label: 'Price',
          data: data.prices,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1
        }
      ]
    };
    
    // Add volume data if available
    if (data.volumes) {
      chartData.datasets.push({
        label: 'Volume',
        data: data.volumes,
        type: 'bar',
        yAxisID: 'volume',
        backgroundColor: 'rgba(139, 148, 158, 0.3)',
        borderColor: 'rgba(139, 148, 158, 0.5)',
        borderWidth: 1
      });
    }
    
    // Chart configuration
    const config = {
      type: 'line',
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            backgroundColor: '#21262d',
            titleColor: '#ffffff',
            bodyColor: '#c9d1d9',
            borderColor: '#30363d',
            borderWidth: 1,
            callbacks: {
              label: function(context) {
                if (context.dataset.label === 'Volume') {
                  return `Volume: ${context.parsed.y.toLocaleString()}`;
                }
                return `Price: $${context.parsed.y.toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            grid: {
              color: 'rgba(139, 148, 158, 0.1)'
            }
          },
          y: {
            display: true,
            position: 'left',
            grid: {
              color: 'rgba(139, 148, 158, 0.1)'
            },
            ticks: {
              callback: function(value) {
                return '$' + value.toFixed(2);
              }
            }
          }
        },
        elements: {
          point: {
            radius: 0,
            hoverRadius: 5
          }
        }
      }
    };
    
    // Add volume scale if volume data exists
    if (data.volumes) {
      config.options.scales.volume = {
        type: 'linear',
        display: false,
        position: 'right',
        max: Math.max(...data.volumes) * 4,
        grid: {
          drawOnChartArea: false
        }
      };
    }
    
    // Create chart
    this.chart = new Chart(ctx, config);
    
    // Add mobile touch gestures
    if (this.isMobile()) {
      this.addChartTouchGestures(canvas);
    }
  }
  
  updateTradingSignals(data) {
    const signalsContainer = document.getElementById('tradingSignals');
    if (!signalsContainer || !data.individual_signals) return;
    
    let html = '<div class="signals-timeline">';
    
    Object.entries(data.individual_signals).forEach(([name, signal]) => {
      const signalClass = signal.signal.toLowerCase();
      const confidence = (signal.confidence * 100).toFixed(1);
      
      html += `
        <div class="signal-item ${signalClass}">
          <div class="signal-header">
            <div class="signal-indicator ${signalClass}"></div>
            <div class="signal-name">${name}</div>
            <div class="signal-value">${signal.signal}</div>
          </div>
          <div class="signal-confidence">${confidence}% confidence</div>
        </div>
      `;
    });
    
    // Overall signal
    if (data.overall_signal) {
      const overallClass = data.overall_signal.toLowerCase();
      const overallConfidence = (data.overall_confidence * 100).toFixed(1);
      
      html += `
        <div class="signal-item ${overallClass}" style="border: 2px solid; margin-top: 1rem;">
          <div class="signal-header">
            <div class="signal-indicator ${overallClass}"></div>
            <div class="signal-name"><strong>Overall Signal</strong></div>
            <div class="signal-value"><strong>${data.overall_signal}</strong></div>
          </div>
          <div class="signal-confidence"><strong>${overallConfidence}% confidence</strong></div>
        </div>
      `;
    }
    
    html += '</div>';
    signalsContainer.innerHTML = html;
  }
  
  updateOracleDisplay(data) {
    const oracleContainer = document.getElementById('oracleInsights');
    if (!oracleContainer) return;
    
    oracleContainer.innerHTML = `
      <div class="oracle-mode">
        <div class="oracle-content">
          <h3 class="oracle-title">Oracle Insights for ${data.ticker}</h3>
          <div class="oracle-state">${data.emotional_state}</div>
          <div class="oracle-narrative">"${data.mystical_narrative}"</div>
          
          <div class="oracle-insights">
            <div class="oracle-insight">
              <div class="oracle-insight-label">Energy Level</div>
              <div class="oracle-insight-value">${(data.energy_level * 100).toFixed(1)}%</div>
            </div>
            <div class="oracle-insight">
              <div class="oracle-insight-label">Archetype</div>
              <div class="oracle-insight-value">${data.archetype_symbol}</div>
            </div>
            <div class="oracle-insight">
              <div class="oracle-insight-label">Oracle Confidence</div>
              <div class="oracle-insight-value">${(data.oracle_confidence * 100).toFixed(1)}%</div>
            </div>
          </div>
          
          <div class="oracle-wisdom mt-3">
            <p><em>"${data.market_wisdom}"</em></p>
          </div>
        </div>
      </div>
    `;
  }
  
  // Utility functions
  formatModelName(modelName) {
    const names = {
      'random_forest': 'Random Forest',
      'lstm': 'LSTM Neural Network',
      'xgboost': 'XGBoost'
    };
    return names[modelName] || modelName;
  }
  
  showError(message) {
    this.showNotification(message, 'error');
  }
  
  showSuccess(message) {
    this.showNotification(message, 'success');
  }
  
  showNotification(message, type = 'info') {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    
    this.state.notifications.unshift(notification);
    this.displayNotification(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      this.removeNotification(notification.id);
    }, 5000);
  }
  
  displayNotification(notification) {
    const container = document.getElementById('notificationContainer') || this.createNotificationContainer();
    
    const element = document.createElement('div');
    element.className = `alert alert-${notification.type} notification slide-in-up`;
    element.id = `notification-${notification.id}`;
    element.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span>${notification.message}</span>
        <button type="button" class="btn-close" onclick="app.removeNotification(${notification.id})">
          <i class="fas fa-times"></i>
        </button>
      </div>
    `;
    
    container.prepend(element);
  }
  
  removeNotification(id) {
    const element = document.getElementById(`notification-${id}`);
    if (element) {
      element.remove();
    }
    
    this.state.notifications = this.state.notifications.filter(n => n.id !== id);
  }
  
  createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notificationContainer';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 1050;
      max-width: 400px;
    `;
    document.body.appendChild(container);
    return container;
  }
  
  toggleTheme() {
    const newTheme = this.state.currentTheme === 'dark' ? 'light' : 'dark';
    this.state.currentTheme = newTheme;
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.innerHTML = newTheme === 'dark' ? 
        '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
    
    // Update chart colors if chart exists
    if (this.chart) {
      this.updateChartTheme();
    }
  }
  
  updateChartTheme() {
    const isDark = this.state.currentTheme === 'dark';
    Chart.defaults.color = isDark ? '#c9d1d9' : '#1e293b';
    Chart.defaults.borderColor = isDark ? 'rgba(139, 148, 158, 0.2)' : 'rgba(30, 41, 59, 0.2)';
    
    if (this.chart) {
      this.chart.update();
    }
  }
  
  toggleMobileMenu() {
    const mobileNav = document.getElementById('mobileNav');
    const mobileNavOverlay = document.getElementById('mobileNavOverlay');
    
    if (mobileNav && mobileNavOverlay) {
      mobileNav.classList.add('active');
      mobileNavOverlay.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }
  
  closeMobileMenu() {
    const mobileNav = document.getElementById('mobileNav');
    const mobileNavOverlay = document.getElementById('mobileNavOverlay');
    
    if (mobileNav && mobileNavOverlay) {
      mobileNav.classList.remove('active');
      mobileNavOverlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
  
  // Mobile-specific functions
  isMobile() {
    return window.innerWidth <= 768;
  }
  
  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent);
  }
  
  setViewportHeight() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
  }
  
  setupTouchGestures() {
    // Implement swipe gestures for mobile
    let touchStartX = 0;
    let touchStartY = 0;
    
    document.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', (e) => {
      if (!touchStartX || !touchStartY) return;
      
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      
      const deltaX = touchStartX - touchEndX;
      const deltaY = touchStartY - touchEndY;
      
      // Horizontal swipe
      if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
        if (deltaX > 0) {
          // Swipe left
          this.handleSwipeLeft();
        } else {
          // Swipe right
          this.handleSwipeRight();
        }
      }
      
      touchStartX = 0;
      touchStartY = 0;
    });
  }
  
  handleSwipeLeft() {
    // Could be used for navigation or dismissing panels
    console.log('Swipe left detected');
  }
  
  handleSwipeRight() {
    // Could be used for opening menu or panels
    if (this.isMobile()) {
      this.toggleMobileMenu();
    }
  }
  
  setupPullToRefresh() {
    if (!this.isMobile()) return;
    
    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    
    document.addEventListener('touchstart', (e) => {
      if (window.scrollY === 0) {
        startY = e.touches[0].clientY;
        isPulling = true;
      }
    });
    
    document.addEventListener('touchmove', (e) => {
      if (!isPulling) return;
      
      currentY = e.touches[0].clientY;
      const pullDistance = currentY - startY;
      
      if (pullDistance > 0 && window.scrollY === 0) {
        e.preventDefault();
        
        if (pullDistance > 100) {
          this.showPullToRefreshIndicator(true);
        } else {
          this.showPullToRefreshIndicator(false);
        }
      }
    });
    
    document.addEventListener('touchend', () => {
      if (isPulling && currentY - startY > 100) {
        this.refreshCurrentAnalysis();
      }
      
      this.hidePullToRefreshIndicator();
      isPulling = false;
      startY = 0;
      currentY = 0;
    });
  }
  
  showPullToRefreshIndicator(ready) {
    let indicator = document.getElementById('pullToRefreshIndicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'pullToRefreshIndicator';
      indicator.className = 'pull-to-refresh';
      indicator.innerHTML = `
        <div class="pull-to-refresh-content">
          <i class="fas fa-sync-alt pull-to-refresh-icon"></i>
          <span class="pull-to-refresh-text">Pull to refresh</span>
        </div>
      `;
      document.body.prepend(indicator);
    }
    
    indicator.classList.toggle('active', true);
    indicator.classList.toggle('ready', ready);
    
    const text = indicator.querySelector('.pull-to-refresh-text');
    if (text) {
      text.textContent = ready ? 'Release to refresh' : 'Pull to refresh';
    }
  }
  
  hidePullToRefreshIndicator() {
    const indicator = document.getElementById('pullToRefreshIndicator');
    if (indicator) {
      indicator.classList.remove('active', 'ready');
    }
  }
  
  async refreshCurrentAnalysis() {
    if (this.currentTicker) {
      // Clear cache for current ticker
      const cacheKeys = [
        `prediction_${this.currentTicker}`,
        `chart_${this.currentTicker}`,
        `signals_${this.currentTicker}`
      ];
      
      cacheKeys.forEach(key => this.cache.delete(key));
      
      // Re-analyze
      await this.analyzeTicker(this.currentTicker);
      this.showSuccess('Data refreshed successfully');
    }
  }
  
  setupHapticFeedback() {
    if (!('vibrate' in navigator)) return;
    
    // Add haptic feedback to buttons
    document.addEventListener('click', (e) => {
      if (e.target.matches('.btn, .touchable')) {
        this.triggerHapticFeedback('light');
      }
    });
  }
  
  triggerHapticFeedback(type = 'light') {
    if (!('vibrate' in navigator)) return;
    
    const patterns = {
      light: [10],
      medium: [20],
      heavy: [30],
      success: [10, 10, 10],
      error: [50, 20, 50]
    };
    
    navigator.vibrate(patterns[type] || patterns.light);
  }
  
  setupIOSFixes() {
    // Prevent zoom on input focus
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        input.style.fontSize = '16px';
      });
      
      input.addEventListener('blur', () => {
        input.style.fontSize = '';
      });
    });
    
    // Handle iOS viewport changes
    window.addEventListener('orientationchange', () => {
      setTimeout(() => {
        this.setViewportHeight();
      }, 500);
    });
  }
  
  // Utility functions
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
  
  updateLoadingState(isLoading) {
    const searchButton = document.querySelector('#searchForm button');
    if (searchButton) {
      searchButton.disabled = isLoading;
      searchButton.innerHTML = isLoading ? 
        '<i class="fas fa-spinner fa-spin"></i> Analyzing...' : 
        '<i class="fas fa-search"></i> Analyze';
    }
  }
  
  showLoadingStates() {
    // Show shimmer effects
    const containers = ['modelComparison', 'ensemblePrediction', 'tradingSignals'];
    containers.forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        element.innerHTML = '<div class="shimmer" style="height: 100px; border-radius: 8px;"></div>';
      }
    });
  }
  
  hideLoadingStates() {
    // Loading states will be replaced by actual content
  }
  
  updateConnectionStatus() {
    let statusElement = document.getElementById('connectionStatus');
    
    if (!statusElement) {
      statusElement = document.createElement('div');
      statusElement.id = 'connectionStatus';
      statusElement.className = 'connection-status';
      document.body.appendChild(statusElement);
    }
    
    statusElement.className = `connection-status ${this.state.isOnline ? 'online' : 'offline'}`;
    statusElement.textContent = this.state.isOnline ? 'Back online' : 'Offline mode';
    
    if (!this.state.isOnline) {
      statusElement.style.opacity = '1';
      statusElement.style.visibility = 'visible';
    } else {
      setTimeout(() => {
        statusElement.style.opacity = '0';
        statusElement.style.visibility = 'hidden';
      }, 2000);
    }
  }
  
  // Search suggestions and history
  showSearchSuggestions(query) {
    // Implementation for search suggestions
    console.log('Showing suggestions for:', query);
  }
  
  hideSearchSuggestions() {
    // Implementation to hide suggestions
  }
  
  addToSearchHistory(ticker) {
    let history = JSON.parse(localStorage.getItem('searchHistory') || '[]');
    history = history.filter(t => t !== ticker); // Remove if exists
    history.unshift(ticker); // Add to beginning
    history = history.slice(0, 10); // Keep only last 10
    localStorage.setItem('searchHistory', JSON.stringify(history));
  }
  
  loadUserPreferences() {
    // Load user preferences from localStorage
    const preferences = JSON.parse(localStorage.getItem('userPreferences') || '{}');
    
    // Apply preferences
    if (preferences.oracleMode !== undefined) {
      this.state.isOracleMode = preferences.oracleMode;
      const oracleToggle = document.getElementById('oracleToggle');
      if (oracleToggle) {
        oracleToggle.checked = preferences.oracleMode;
      }
    }
  }
  
  saveUserPreferences() {
    const preferences = {
      oracleMode: this.state.isOracleMode,
      theme: this.state.currentTheme
    };
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
  }
  
  loadWatchlist() {
    this.state.watchlist = JSON.parse(localStorage.getItem('watchlist') || '[]');
  }
  
  updateURL(ticker) {
    const url = new URL(window.location);
    url.searchParams.set('ticker', ticker);
    window.history.pushState({}, '', url);
  }
  
  handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + K for search focus
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const searchInput = document.getElementById('searchInput');
      if (searchInput) {
        searchInput.focus();
      }
    }
    
    // Escape to close modals/menus
    if (e.key === 'Escape') {
      this.closeMobileMenu();
    }
  }
  
  updateOracleMode() {
    this.saveUserPreferences();
    
    // Toggle Oracle-specific UI elements
    const oracleElements = document.querySelectorAll('.oracle-mode, .oracle-toggle');
    oracleElements.forEach(element => {
      element.style.display = this.state.isOracleMode ? 'block' : 'none';
    });
  }
  
  async updateOracleInsights(ticker) {
    if (!this.state.isOracleMode) return;
    
    try {
      const insights = await this.fetchOracleInsights(ticker);
      this.updateOracleDisplay(insights);
    } catch (error) {
      console.error('Failed to fetch Oracle insights:', error);
    }
  }
  
  initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
      const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
      tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
      });
    }
  }
  
  initializeModals() {
    // Initialize any modals
  }
  
  // Service Worker message handling
  handleServiceWorkerMessage(data) {
    if (data.type === 'CACHE_UPDATED') {
      this.showNotification('App updated and cached for offline use', 'success');
    }
  }
  
  showUpdateNotification() {
    this.showNotification('A new version is available. Refresh to update.', 'info');
  }
  
  setupPushNotifications() {
    // Implementation for push notifications
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      // Setup push subscription
    }
  }
  
  syncOfflineData() {
    // Sync any data that was stored while offline
    console.log('Syncing offline data...');
  }
  
  setupSwipeNavigation() {
    // Setup swipe navigation between sections
  }
  
  addChartTouchGestures(canvas) {
    // Add pinch-to-zoom and pan gestures for charts on mobile
    let initialDistance = 0;
    let initialScale = 1;
    
    canvas.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        initialDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
      }
    });
    
    canvas.addEventListener('touchmove', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        
        if (initialDistance > 0) {
          const scale = currentDistance / initialDistance;
          // Apply zoom to chart
          if (this.chart && Math.abs(scale - 1) > 0.1) {
            // Implement chart zoom
          }
        }
      }
    });
  }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.app = new FullStockApp();
});
