// Main application JavaScript
class FullStockApp {
    constructor() {
        this.currentSymbol = null;
        this.websocket = null;
        this.charts = {};
        this.theme = localStorage.getItem('theme') || 'dark';
        this.init();
    }

    async init() {
        console.log('Initializing FullStock AI vNext Ultimate...');
        
        // Initialize theme
        this.initTheme();
        
        // Initialize WebSocket connection
        this.initWebSocket();
        
        // Bind event listeners
        this.bindEventListeners();
        
        // Initialize PWA
        this.initPWA();
        
        // Load market overview
        await this.loadMarketOverview();
        
        // Initialize floating insights panel
        this.initFloatingInsights();
        
        // Start market pulse
        this.startMarketPulse();
        
        console.log('FullStock AI initialized successfully');
    }

    initTheme() {
        document.documentElement.setAttribute('data-bs-theme', this.theme);
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    initWebSocket() {
        if (typeof io !== 'undefined') {
            this.websocket = io();
            
            this.websocket.on('connect', () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus(true);
            });
            
            this.websocket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus(false);
            });
            
            this.websocket.on('price_update', (data) => {
                this.handlePriceUpdate(data);
            });
            
            this.websocket.on('market_pulse', (data) => {
                this.updateMarketPulse(data);
            });
            
            this.websocket.on('alert_triggered', (data) => {
                this.showAlert(data);
            });
        }
    }

    bindEventListeners() {
        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Symbol input
        const symbolInput = document.getElementById('symbolInput');
        if (symbolInput) {
            symbolInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.predictStock();
                }
            });
        }

        // Predict button
        const predictBtn = document.getElementById('predictBtn');
        if (predictBtn) {
            predictBtn.addEventListener('click', () => {
                this.predictStock();
            });
        }

        // Oracle mode toggle
        const oracleMode = document.getElementById('oracleMode');
        if (oracleMode) {
            oracleMode.addEventListener('change', (e) => {
                this.toggleOracleMode(e.target.checked);
            });
        }

        // Floating insights panel toggle
        const toggleInsightPanel = document.getElementById('toggleInsightPanel');
        if (toggleInsightPanel) {
            toggleInsightPanel.addEventListener('click', () => {
                this.toggleFloatingInsights();
            });
        }

        // Refresh prediction
        const refreshPrediction = document.getElementById('refreshPrediction');
        if (refreshPrediction) {
            refreshPrediction.addEventListener('click', () => {
                if (this.currentSymbol) {
                    this.predictStock(this.currentSymbol);
                }
            });
        }

        // Export data
        const exportData = document.getElementById('exportData');
        if (exportData) {
            exportData.addEventListener('click', () => {
                this.exportPredictionData();
            });
        }

        // Add to watchlist
        const addToWatchlist = document.getElementById('addToWatchlist');
        if (addToWatchlist) {
            addToWatchlist.addEventListener('click', () => {
                this.showAddWatchlistModal();
            });
        }
    }

    initPWA() {
        // PWA install prompt
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            const pwaInstallBtn = document.getElementById('pwaInstallBtn');
            if (pwaInstallBtn) {
                pwaInstallBtn.classList.remove('d-none');
                pwaInstallBtn.addEventListener('click', async () => {
                    if (deferredPrompt) {
                        deferredPrompt.prompt();
                        const { outcome } = await deferredPrompt.userChoice;
                        console.log(`PWA install outcome: ${outcome}`);
                        deferredPrompt = null;
                        pwaInstallBtn.classList.add('d-none');
                    }
                });
            }
        });

        // Register service worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/sw.js')
                    .then((registration) => {
                        console.log('SW registered: ', registration);
                    })
                    .catch((registrationError) => {
                        console.log('SW registration failed: ', registrationError);
                    });
            });
        }
    }

    toggleTheme() {
        this.theme = this.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', this.theme);
        document.documentElement.setAttribute('data-bs-theme', this.theme);
        
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = this.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    updateConnectionStatus(connected) {
        const connectionStatus = document.getElementById('connectionStatus');
        if (connectionStatus) {
            connectionStatus.className = connected 
                ? 'fas fa-wifi text-success' 
                : 'fas fa-wifi text-danger';
            connectionStatus.title = connected ? 'Connected' : 'Disconnected';
        }
    }

    async loadMarketOverview() {
        try {
            const response = await fetch('/api/market-status');
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading market overview:', data.error);
                return;
            }
            
            this.renderMarketOverview(data);
            
        } catch (error) {
            console.error('Error loading market overview:', error);
        }
    }

    renderMarketOverview(data) {
        const container = document.getElementById('marketOverview');
        if (!container) return;

        let html = '';
        
        // Render indices
        if (data.indices) {
            Object.entries(data.indices).forEach(([symbol, info]) => {
                const changeClass = info.change >= 0 ? 'text-success' : 'text-danger';
                const changeIcon = info.change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
                
                html += `
                    <div class="col-md-3 mb-3">
                        <div class="market-card">
                            <div class="market-symbol">${symbol}</div>
                            <div class="market-price">$${info.price.toFixed(2)}</div>
                            <div class="market-change ${changeClass}">
                                <i class="fas ${changeIcon} me-1"></i>
                                ${info.change.toFixed(2)}%
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        container.innerHTML = html;
        
        // Update last updated time
        const lastUpdated = document.getElementById('lastUpdated');
        if (lastUpdated) {
            lastUpdated.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
        }
    }

    async predictStock(symbol = null) {
        const symbolInput = document.getElementById('symbolInput');
        const targetSymbol = symbol || symbolInput?.value?.trim().toUpperCase();
        
        if (!targetSymbol) {
            this.showToast('Please enter a stock symbol', 'warning');
            return;
        }

        this.currentSymbol = targetSymbol;
        this.showLoadingOverlay(true);
        
        try {
            const response = await fetch(`/api/predict/${targetSymbol}`);
            const data = await response.json();
            
            if (data.error) {
                this.showToast(data.error, 'error');
                return;
            }
            
            // Display prediction results
            this.displayPredictionResults(data);
            
            // Load technical analysis
            await this.loadTechnicalAnalysis(targetSymbol);
            
            // Update floating insights
            this.updateFloatingInsights(data);
            
            // Join WebSocket room for real-time updates
            if (this.websocket) {
                this.websocket.emit('join_watchlist', { symbol: targetSymbol });
            }
            
        } catch (error) {
            console.error('Error predicting stock:', error);
            this.showToast('Error loading prediction', 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    displayPredictionResults(data) {
        const resultsContainer = document.getElementById('predictionResults');
        if (!resultsContainer) return;

        resultsContainer.style.display = 'block';
        
        // Update current symbol
        const currentSymbolSpan = document.getElementById('currentSymbol');
        if (currentSymbolSpan) {
            currentSymbolSpan.textContent = data.symbol;
        }

        // Update model predictions
        this.updateModelPredictions(data);
        
        // Update chart
        this.updatePredictionChart(data);
    }

    updateModelPredictions(data) {
        const predictions = data.predictions || {};
        const currentPrice = data.current_price || 0;

        // Random Forest
        if (predictions.random_forest) {
            this.updateModelCard('rf', predictions.random_forest, currentPrice);
        }

        // XGBoost
        if (predictions.xgboost) {
            this.updateModelCard('xgb', predictions.xgboost, currentPrice);
        }

        // LSTM
        if (predictions.lstm) {
            this.updateModelCard('lstm', predictions.lstm, currentPrice);
        }

        // Ensemble
        if (predictions.ensemble) {
            this.updateEnsembleCard(predictions.ensemble, currentPrice);
        }
    }

    updateModelCard(modelType, prediction, currentPrice) {
        const predictionValue = prediction.prediction || 0;
        const confidence = prediction.confidence || 0;
        const change = ((predictionValue - currentPrice) / currentPrice) * 100;

        // Update prediction value
        const predElement = document.getElementById(`${modelType}Prediction`);
        if (predElement) {
            predElement.textContent = `$${predictionValue.toFixed(2)}`;
        }

        // Update change percentage
        const changeElement = document.getElementById(`${modelType}Change`);
        if (changeElement) {
            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            changeElement.className = `prediction-change ${changeClass}`;
            changeElement.innerHTML = `<i class="fas ${changeIcon} me-1"></i>${change.toFixed(2)}%`;
        }

        // Update confidence
        const confidenceFill = document.getElementById(`${modelType}Confidence`);
        const confidenceText = document.getElementById(`${modelType}ConfidenceText`);
        if (confidenceFill && confidenceText) {
            const confidencePercent = Math.round(confidence * 100);
            confidenceFill.style.width = `${confidencePercent}%`;
            confidenceText.textContent = `${confidencePercent}%`;
        }

        // Update status
        const statusElement = document.getElementById(`${modelType}Status`);
        if (statusElement) {
            statusElement.textContent = 'ACTIVE';
            statusElement.className = 'model-badge bg-success';
        }
    }

    updateEnsembleCard(ensemble, currentPrice) {
        const predictionValue = ensemble.prediction || 0;
        const confidence = ensemble.confidence || 0;
        const agreement = ensemble.model_agreement || 0;
        const change = ((predictionValue - currentPrice) / currentPrice) * 100;

        // Update ensemble prediction
        const ensemblePred = document.getElementById('ensemblePrediction');
        if (ensemblePred) {
            ensemblePred.textContent = `$${predictionValue.toFixed(2)}`;
        }

        // Update ensemble change
        const ensembleChange = document.getElementById('ensembleChange');
        if (ensembleChange) {
            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
            const changeIcon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            ensembleChange.className = `ensemble-change ${changeClass}`;
            ensembleChange.innerHTML = `<i class="fas ${changeIcon} me-1"></i>${change.toFixed(2)}%`;
        }

        // Update confidence
        const ensembleConf = document.getElementById('ensembleConfidence');
        if (ensembleConf) {
            ensembleConf.textContent = `${Math.round(confidence * 100)}%`;
        }

        // Update agreement
        const agreementFill = document.getElementById('agreementFill');
        const agreementPercent = document.getElementById('agreementPercent');
        if (agreementFill && agreementPercent) {
            const agreementValue = Math.round(agreement * 100);
            agreementFill.style.width = `${agreementValue}%`;
            agreementPercent.textContent = `${agreementValue}%`;
            
            // Color code agreement level
            if (agreementValue >= 80) {
                agreementFill.className = 'agreement-fill bg-success';
            } else if (agreementValue >= 60) {
                agreementFill.className = 'agreement-fill bg-warning';
            } else {
                agreementFill.className = 'agreement-fill bg-danger';
            }
        }
    }

    async updatePredictionChart(data) {
        try {
            const response = await fetch(`/api/chart/${data.symbol}`);
            const chartData = await response.json();
            
            if (chartData.error) {
                console.error('Error loading chart data:', chartData.error);
                return;
            }
            
            this.renderPredictionChart(chartData);
            
        } catch (error) {
            console.error('Error updating chart:', error);
        }
    }

    renderPredictionChart(chartData) {
        const canvas = document.getElementById('priceChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        if (this.charts.price) {
            this.charts.price.destroy();
        }

        const config = {
            type: 'line',
            data: {
                labels: chartData.labels || [],
                datasets: [{
                    label: 'Price',
                    data: chartData.prices || [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price History with Predictions',
                        color: this.theme === 'dark' ? '#fff' : '#000'
                    },
                    legend: {
                        labels: {
                            color: this.theme === 'dark' ? '#fff' : '#000'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: this.theme === 'dark' ? '#fff' : '#000'
                        },
                        grid: {
                            color: this.theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: this.theme === 'dark' ? '#fff' : '#000'
                        },
                        grid: {
                            color: this.theme === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        };

        this.charts.price = new Chart(ctx, config);
    }

    async loadTechnicalAnalysis(symbol) {
        const technicalContainer = document.getElementById('technicalAnalysis');
        if (!technicalContainer) return;

        technicalContainer.style.display = 'block';
        
        // This would be implemented based on the technical indicators from the prediction API
        // For now, we'll show a placeholder
        const indicatorsDiv = document.getElementById('technicalIndicators');
        const sentimentDiv = document.getElementById('sentimentAnalysis');
        
        if (indicatorsDiv) {
            indicatorsDiv.innerHTML = `
                <div class="indicator-item">
                    <span class="indicator-name">RSI:</span>
                    <span class="indicator-value">65.2</span>
                    <span class="badge bg-warning">Neutral</span>
                </div>
                <div class="indicator-item">
                    <span class="indicator-name">MACD:</span>
                    <span class="indicator-value">1.23</span>
                    <span class="badge bg-success">Bullish</span>
                </div>
                <div class="indicator-item">
                    <span class="indicator-name">Moving Avg:</span>
                    <span class="indicator-value">Above</span>
                    <span class="badge bg-success">Bullish</span>
                </div>
            `;
        }
        
        if (sentimentDiv) {
            sentimentDiv.innerHTML = `
                <div class="sentiment-score">
                    <div class="sentiment-value positive">+0.15</div>
                    <div class="sentiment-label">Overall Sentiment</div>
                </div>
                <div class="news-count">
                    <small class="text-muted">Based on 12 recent articles</small>
                </div>
            `;
        }
    }

    toggleOracleMode(enabled) {
        const oracleInsights = document.getElementById('oracleInsights');
        if (!oracleInsights) return;

        if (enabled && this.currentSymbol) {
            this.loadOracleInsights(this.currentSymbol);
        } else {
            oracleInsights.style.display = 'none';
        }
    }

    async loadOracleInsights(symbol) {
        try {
            const response = await fetch(`/api/oracle/${symbol}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading oracle insights:', data.error);
                return;
            }
            
            this.displayOracleInsights(data);
            
        } catch (error) {
            console.error('Error loading oracle insights:', error);
        }
    }

    displayOracleInsights(data) {
        const oracleInsights = document.getElementById('oracleInsights');
        if (!oracleInsights) return;

        oracleInsights.style.display = 'block';
        
        // Update oracle state badge
        const stateBadge = document.getElementById('oracleStateBadge');
        if (stateBadge) {
            stateBadge.textContent = data.oracle_state || 'MYSTICAL';
        }

        // Update archetype
        const archetypeSymbol = document.getElementById('archetypeSymbol');
        const archetypeName = document.getElementById('archetypeName');
        if (archetypeSymbol && archetypeName) {
            // Extract symbol from archetype description
            const symbols = {'PHOENIX': '🔥', 'DRAGON': '🐉', 'EAGLE': '🦅', 'WOLF': '🐺', 'SERPENT': '🐍', 'TITAN': '🏛️', 'SPHINX': '🗿', 'ORACLE': '🔮'};
            archetypeSymbol.textContent = symbols[data.archetype] || '🔮';
            archetypeName.textContent = data.archetype || 'ORACLE';
        }

        // Update narrative
        const narrative = document.getElementById('oracleNarrative');
        if (narrative) {
            narrative.textContent = data.narrative || 'The Oracle contemplates the cosmic patterns...';
        }

        // Update prophecy
        const prophecy = document.getElementById('prophecyText');
        if (prophecy) {
            prophecy.textContent = data.prophecy || 'The future reveals itself to those who seek wisdom...';
        }

        // Update ritual
        const ritual = document.getElementById('ritualText');
        if (ritual) {
            ritual.textContent = data.ritual_recommendation || 'Meditate with focused intention...';
        }

        // Update mystical metrics
        const metrics = data.mystical_metrics || {};
        this.updateMysticalMetrics(metrics);
    }

    updateMysticalMetrics(metrics) {
        const elements = ['spiritual', 'karmic', 'ethereal', 'astral'];
        const keys = ['spiritual_momentum', 'karmic_balance', 'ethereal_volatility', 'astral_volume'];
        
        elements.forEach((element, index) => {
            const valueElement = document.getElementById(`${element}Momentum`) || 
                                document.getElementById(element + keys[index].split('_')[1]);
            if (valueElement) {
                const value = metrics[keys[index]] || 0;
                valueElement.textContent = Math.round(value);
            }
        });
    }

    initFloatingInsights() {
        const floatingPanel = document.getElementById('floatingInsight');
        if (floatingPanel) {
            // Make it draggable on desktop
            if (window.innerWidth > 768) {
                this.makeDraggable(floatingPanel);
            }
            
            // Show by default
            floatingPanel.style.display = 'block';
        }
    }

    makeDraggable(element) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        const header = element.querySelector('.card-body');
        
        if (header) {
            header.style.cursor = 'move';
            header.onmousedown = dragMouseDown;
        }

        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    updateFloatingInsights(data) {
        const activeModel = document.getElementById('activeModel');
        const modelConfidence = document.getElementById('modelConfidence');
        const oracleState = document.getElementById('oracleState');

        if (activeModel && data.predictions) {
            const models = Object.keys(data.predictions);
            activeModel.textContent = models.length > 0 ? models[0].toUpperCase() : '-';
        }

        if (modelConfidence && data.predictions?.ensemble) {
            const confidence = Math.round((data.predictions.ensemble.confidence || 0) * 100);
            modelConfidence.textContent = `${confidence}%`;
        }

        if (oracleState) {
            oracleState.textContent = 'ACTIVE';
        }
    }

    toggleFloatingInsights() {
        const floatingPanel = document.getElementById('floatingInsight');
        const insightContent = document.getElementById('insightContent');
        
        if (floatingPanel && insightContent) {
            const isVisible = insightContent.style.display !== 'none';
            insightContent.style.display = isVisible ? 'none' : 'block';
            
            const toggleBtn = document.getElementById('toggleInsightPanel');
            const icon = toggleBtn?.querySelector('i');
            if (icon) {
                icon.className = isVisible ? 'fas fa-eye-slash' : 'fas fa-eye';
            }
        }
    }

    startMarketPulse() {
        // Request market pulse data
        if (this.websocket) {
            this.websocket.emit('get_market_pulse');
            
            // Request updates every 30 seconds
            setInterval(() => {
                this.websocket.emit('get_market_pulse');
            }, 30000);
        }
    }

    updateMarketPulse(data) {
        const pulseContent = document.getElementById('pulseContent');
        if (!pulseContent) return;

        let html = '';
        
        // Add indices
        if (data.indices) {
            Object.entries(data.indices).forEach(([symbol, info]) => {
                const changeClass = info.change >= 0 ? 'text-success' : 'text-danger';
                html += `
                    <div class="pulse-item">
                        <span class="pulse-symbol">${symbol}</span>
                        <span class="pulse-change ${changeClass}">${info.change.toFixed(1)}%</span>
                    </div>
                `;
            });
        }

        // Add crypto
        if (data.crypto) {
            Object.entries(data.crypto).forEach(([symbol, info]) => {
                const changeClass = info.change >= 0 ? 'text-success' : 'text-danger';
                const cryptoSymbol = symbol.replace('-USD', '');
                html += `
                    <div class="pulse-item crypto">
                        <span class="pulse-symbol">${cryptoSymbol}</span>
                        <span class="pulse-change ${changeClass}">${info.change.toFixed(1)}%</span>
                    </div>
                `;
            });
        }

        pulseContent.innerHTML = html;
    }

    handlePriceUpdate(data) {
        // Update floating insights if it's the current symbol
        if (this.currentSymbol && data.symbol === this.currentSymbol) {
            this.updateCurrentPriceDisplay(data);
        }

        // Update watchlist items
        this.updateWatchlistItem(data);
    }

    updateCurrentPriceDisplay(data) {
        // This would update the current price displays in the prediction results
        const priceElements = document.querySelectorAll(`[data-symbol="${data.symbol}"] .current-price`);
        priceElements.forEach(element => {
            element.textContent = `$${data.price.toFixed(2)}`;
            
            // Add visual effect for price changes
            const changeClass = data.change_percent >= 0 ? 'price-up' : 'price-down';
            element.classList.add(changeClass);
            setTimeout(() => {
                element.classList.remove(changeClass);
            }, 1000);
        });
    }

    updateWatchlistItem(data) {
        const watchlistItem = document.querySelector(`[data-watchlist-symbol="${data.symbol}"]`);
        if (watchlistItem) {
            const priceElement = watchlistItem.querySelector('.watchlist-price');
            const changeElement = watchlistItem.querySelector('.watchlist-change');
            
            if (priceElement) {
                priceElement.textContent = `$${data.price.toFixed(2)}`;
            }
            
            if (changeElement) {
                const changeClass = data.change_percent >= 0 ? 'text-success' : 'text-danger';
                const changeIcon = data.change_percent >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
                changeElement.className = `watchlist-change ${changeClass}`;
                changeElement.innerHTML = `<i class="fas ${changeIcon} me-1"></i>${data.change_percent.toFixed(2)}%`;
            }
        }
    }

    showLoadingOverlay(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toastId = 'toast-' + Date.now();
        const bgClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';

        const toastHtml = `
            <div class="toast ${bgClass} text-white" id="${toastId}" role="alert">
                <div class="toast-header ${bgClass} text-white border-0">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong class="me-auto">FullStock AI</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove toast after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    showAlert(alertData) {
        const message = `${alertData.symbol} has ${alertData.type.includes('above') ? 'risen above' : 'fallen below'} $${alertData.threshold}. Current price: $${alertData.current_price}`;
        this.showToast(message, 'warning');
    }

    showAddWatchlistModal() {
        // This would show a modal for adding items to watchlist
        const symbol = this.currentSymbol || '';
        const symbolInput = prompt('Enter symbol to add to watchlist:', symbol);
        
        if (symbolInput) {
            this.addToWatchlist(symbolInput.trim().toUpperCase());
        }
    }

    async addToWatchlist(symbol) {
        try {
            const response = await fetch('/api/watchlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    asset_type: 'stock'
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showToast(data.error, 'error');
            } else {
                this.showToast(`${symbol} added to watchlist`, 'success');
                this.loadWatchlist(); // Refresh watchlist display
            }
            
        } catch (error) {
            console.error('Error adding to watchlist:', error);
            this.showToast('Error adding to watchlist', 'error');
        }
    }

    async loadWatchlist() {
        try {
            const response = await fetch('/api/watchlist');
            const data = await response.json();
            
            if (data.watchlist) {
                this.renderWatchlist(data.watchlist);
            }
            
        } catch (error) {
            console.error('Error loading watchlist:', error);
        }
    }

    renderWatchlist(watchlist) {
        const container = document.getElementById('watchlistContainer');
        if (!container) return;

        if (watchlist.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-star fa-2x mb-2"></i>
                    <p>Your watchlist is empty. Add symbols to track them in real-time.</p>
                </div>
            `;
            return;
        }

        let html = '';
        watchlist.forEach(item => {
            html += `
                <div class="watchlist-item" data-watchlist-symbol="${item.symbol}">
                    <div class="watchlist-symbol">${item.symbol}</div>
                    <div class="watchlist-price">$0.00</div>
                    <div class="watchlist-change">0.00%</div>
                    <div class="watchlist-actions">
                        <button class="btn btn-sm btn-outline-primary" onclick="app.predictStock('${item.symbol}')">
                            <i class="fas fa-chart-line"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="app.removeFromWatchlist(${item.id})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

        // Join WebSocket rooms for watchlist items
        if (this.websocket) {
            watchlist.forEach(item => {
                this.websocket.emit('join_watchlist', { symbol: item.symbol });
            });
        }
    }

    async removeFromWatchlist(itemId) {
        try {
            const response = await fetch(`/api/watchlist/${itemId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.showToast(data.error, 'error');
            } else {
                this.showToast('Removed from watchlist', 'success');
                this.loadWatchlist(); // Refresh watchlist display
            }
            
        } catch (error) {
            console.error('Error removing from watchlist:', error);
            this.showToast('Error removing from watchlist', 'error');
        }
    }

    exportPredictionData() {
        if (!this.currentSymbol) {
            this.showToast('No prediction data to export', 'warning');
            return;
        }

        // This would gather current prediction data and export as CSV/JSON
        const data = {
            symbol: this.currentSymbol,
            timestamp: new Date().toISOString(),
            predictions: {
                // Would contain actual prediction data
            }
        };

        const dataStr = JSON.stringify(data, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `${this.currentSymbol}_predictions_${new Date().toISOString().split('T')[0]}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FullStockApp();
});
