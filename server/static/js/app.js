/**
 * FullStock AI vNext Ultimate - Frontend Application
 * Advanced Stock Prediction Platform with Real-time Features
 */

class FullStockApp {
    constructor() {
        this.cache = new Map();
        this.socket = null;
        this.chart = null;
        this.state = {
            currentTicker: null,
            isLoading: false,
            oracleMode: false
        };
    }

    init() {
        this.initializeSocketIO();
        this.bindEvents();
        this.loadFromURL();
        console.log('FullStock AI vNext Ultimate initialized');
    }

    initializeSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
        });

        this.socket.on('price_update', (data) => {
            this.handlePriceUpdate(data);
        });

        this.socket.on('prediction_update', (data) => {
            this.handlePredictionUpdate(data);
        });
    }

    bindEvents() {
        // Analyze button
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeTicker();
        });

        // Enter key on input
        document.getElementById('tickerInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.analyzeTicker();
            }
        });

        // Oracle mode toggle
        document.getElementById('oracleToggle').addEventListener('change', (e) => {
            this.state.oracleMode = e.target.checked;
            this.toggleOraclePanel(e.target.checked);
        });
    }

    async analyzeTicker() {
        const ticker = document.getElementById('tickerInput').value.toUpperCase().trim();
        
        if (!ticker) {
            this.showError('Please enter a ticker symbol');
            return;
        }

        this.state.currentTicker = ticker;
        this.state.isLoading = true;
        this.showLoading(true);
        this.hideResults();

        try {
            // Fetch prediction data
            const prediction = await this.fetchPrediction(ticker);
            
            if (prediction.error) {
                throw new Error(prediction.error);
            }

            console.log('Analysis successful, updating UI...');
            
            // Update UI with prediction data
            this.updatePredictionDisplay(prediction);
            
            // Show results immediately after updating prediction display
            this.showResults();
            
            // Fetch and display chart
            await this.updateChart(ticker);
            
            // Oracle mode insights
            if (this.state.oracleMode) {
                await this.fetchOracleInsights(ticker);
            }

            this.updateURL(ticker);

        } catch (error) {
            console.error('Analysis error:', error);
            this.showError(`Analysis failed: ${error.message || 'Unknown error'}`);
        } finally {
            this.state.isLoading = false;
            this.showLoading(false);
        }
    }

    async fetchPrediction(ticker) {
        const cacheKey = `prediction_${ticker}`;
        
        // Check cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 5 * 60 * 1000) { // 5 minutes
                return cached.data;
            }
        }

        try {
            const response = await fetch(`/api/predict/${ticker}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Cache the result
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });

            return data;
        } catch (error) {
            console.error('Prediction fetch error:', error);
            throw error;
        }
    }

    async fetchOracleInsights(ticker) {
        try {
            const response = await fetch(`/api/oracle/mystical/${ticker}`);
            if (response.ok) {
                const oracleData = await response.json();
                this.updateOracleDisplay(oracleData);
            }
        } catch (error) {
            console.error('Oracle insights error:', error);
        }
    }

    updatePredictionDisplay(data) {
        console.log('Updating prediction display with data:', data);
        
        // Current price
        const currentPriceEl = document.getElementById('currentPrice');
        if (currentPriceEl && data.current_price) {
            console.log('Setting current price:', data.current_price);
            currentPriceEl.textContent = `$${data.current_price.toFixed(2)}`;
            console.log('Current price element text now:', currentPriceEl.textContent);
        } else {
            console.error('Current price element not found or no price data');
        }
        
        // Price change
        const change = data.price_change || 0;
        const changePercent = data.change_percent || 0;
        const changeElement = document.getElementById('priceChange');
        if (changeElement) {
            changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
            changeElement.className = change >= 0 ? 'text-success' : 'text-danger';
        }

        // Individual model predictions
        if (data.predictions) {
            console.log('Updating individual predictions:', data.predictions);
            
            // Random Forest
            const rfElement = document.getElementById('rfPrediction');
            const rfConfElement = document.getElementById('rfConfidence');
            if (rfElement && data.predictions.random_forest) {
                const rfPrediction = data.predictions.random_forest.prediction;
                const rfConfidence = data.predictions.random_forest.confidence;
                console.log('Setting RF prediction:', rfPrediction);
                rfElement.textContent = rfPrediction ? `$${rfPrediction.toFixed(2)}` : '--';
                console.log('RF element text now:', rfElement.textContent);
                if (rfConfElement) {
                    rfConfElement.textContent = rfConfidence ? `${(rfConfidence * 100).toFixed(1)}% confidence` : '--';
                }
            } else {
                console.error('RF element not found or no RF data');
            }

            // XGBoost
            const xgbElement = document.getElementById('xgbPrediction');
            const xgbConfElement = document.getElementById('xgbConfidence');
            if (xgbElement && data.predictions.xgboost) {
                const xgbPrediction = data.predictions.xgboost.prediction;
                const xgbConfidence = data.predictions.xgboost.confidence;
                xgbElement.textContent = xgbPrediction ? `$${xgbPrediction.toFixed(2)}` : '--';
                if (xgbConfElement) {
                    xgbConfElement.textContent = xgbConfidence ? `${(xgbConfidence * 100).toFixed(1)}% confidence` : '--';
                }
            }

            // LSTM
            const lstmElement = document.getElementById('lstmPrediction');
            const lstmConfElement = document.getElementById('lstmConfidence');
            if (lstmElement) {
                if (data.predictions.lstm && !data.predictions.lstm.error && data.predictions.lstm.prediction) {
                    lstmElement.textContent = `$${data.predictions.lstm.prediction.toFixed(2)}`;
                    if (lstmConfElement) {
                        lstmConfElement.textContent = `${(data.predictions.lstm.confidence * 100).toFixed(1)}% confidence`;
                    }
                } else {
                    lstmElement.textContent = 'Unavailable';
                    if (lstmConfElement) {
                        lstmConfElement.textContent = 'TensorFlow compatibility issue';
                    }
                }
            }
        }

        // Ensemble prediction
        const ensembleElement = document.getElementById('ensemblePrediction');
        const directionElement = document.getElementById('ensembleDirection');
        
        if (ensembleElement && data.predictions?.ensemble) {
            const ensemblePred = data.predictions.ensemble.prediction;
            const ensembleConf = data.predictions.ensemble.confidence;
            
            console.log('Updating ensemble prediction:', ensemblePred, ensembleConf);
            
            if (ensemblePred) {
                ensembleElement.textContent = `$${ensemblePred.toFixed(2)}`;
                
                if (directionElement && data.current_price) {
                    const direction = ensemblePred > data.current_price ? 'BULLISH' : 'BEARISH';
                    const directionClass = direction === 'BULLISH' ? 'text-success' : 'text-danger';
                    directionElement.innerHTML = 
                        `<span class="${directionClass}">${direction}</span> - ${(ensembleConf * 100).toFixed(1)}% confidence`;
                }
            }
        }
    }

    async updateChart(ticker) {
        try {
            const response = await fetch(`/api/chart_data/${ticker}`);
            if (!response.ok) return;

            const chartData = await response.json();
            this.renderChart(chartData);
        } catch (error) {
            console.error('Chart update error:', error);
        }
    }

    renderChart(data) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        const labels = data.dates || [];
        const prices = data.prices || [];
        const predictions = data.predictions || [];

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Price',
                        data: prices,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'Predictions',
                        data: predictions,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        borderDash: [5, 5],
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    updateOracleDisplay(oracleData) {
        if (oracleData) {
            document.getElementById('oracleSymbol').textContent = oracleData.symbol || '🏛️';
            document.getElementById('oracleArchetype').textContent = oracleData.archetype || 'Temple';
            document.getElementById('oracleInsight').textContent = oracleData.insight || 'The market reveals its ancient wisdom...';
            document.getElementById('oracleGuidance').textContent = oracleData.guidance || 'Trust in the patterns that emerge from chaos...';
        }
    }

    toggleOraclePanel(show) {
        const panel = document.getElementById('oraclePanel');
        if (show) {
            panel.classList.remove('d-none');
        } else {
            panel.classList.add('d-none');
        }
    }

    showResults() {
        console.log('Showing results section');
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.classList.remove('d-none');
            console.log('Results section is now visible');
        } else {
            console.error('Results section not found!');
        }
    }

    hideResults() {
        document.getElementById('resultsSection').classList.add('d-none');
    }

    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        if (show) {
            spinner.classList.remove('d-none');
        } else {
            spinner.classList.add('d-none');
        }
    }

    showError(message) {
        console.error('Showing error:', message);
        
        // Create error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show mx-3 mt-3';
        alertDiv.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert after navigation
        const nav = document.querySelector('nav');
        if (nav) {
            nav.insertAdjacentElement('afterend', alertDiv);
        }

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 10000);
    }

    handlePriceUpdate(data) {
        if (data.ticker === this.state.currentTicker) {
            // Update current price display
            const priceElement = document.getElementById('currentPrice');
            if (priceElement && data.price) {
                priceElement.textContent = `$${data.price.toFixed(2)}`;
            }
        }
    }

    handlePredictionUpdate(data) {
        if (data.ticker === this.state.currentTicker) {
            this.updatePredictionDisplay(data);
        }
    }

    updateURL(ticker) {
        const url = new URL(window.location);
        url.searchParams.set('ticker', ticker);
        window.history.pushState({}, '', url);
    }

    loadFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const ticker = urlParams.get('ticker');
        
        if (ticker) {
            document.getElementById('tickerInput').value = ticker;
            this.analyzeTicker();
        }
    }
}

// Make globally available
window.FullStockApp = FullStockApp;