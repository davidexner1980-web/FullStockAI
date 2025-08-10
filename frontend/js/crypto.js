/**
 * FullStock AI Crypto Dashboard - Real Cryptocurrency Data Integration
 * Handles crypto analysis, predictions display, and live crypto updates
 */

let currentCrypto = 'BTC-USD';
let cryptoChart = null;
let isAnalyzingCrypto = false;

/**
 * Initialize Crypto Dashboard
 */
function initializeCryptoDashboard() {
    console.log('Crypto Dashboard initialized');
    
    // Setup event listeners
    setupCryptoEventListeners();
    
    // Initialize WebSocket connection
    if (typeof initializeWebSocket === 'function') {
        initializeWebSocket();
    }
    
    // Setup crypto chart
    initializeCryptoChart();
}

/**
 * Setup Crypto Event Listeners
 */
function setupCryptoEventListeners() {
    const analyzeCryptoBtn = document.getElementById('analyzeCryptoBtn');
    const cryptoInput = document.getElementById('cryptoInput');
    const quickCryptos = document.querySelectorAll('.quick-crypto');
    const cryptoTimeframeBtns = document.querySelectorAll('.crypto-timeframe-btn');

    // Analyze button
    if (analyzeCryptoBtn) {
        analyzeCryptoBtn.addEventListener('click', () => {
            const crypto = cryptoInput.value.trim().toUpperCase();
            if (crypto) {
                analyzeCrypto(crypto);
            }
        });
    }

    // Enter key in input
    if (cryptoInput) {
        cryptoInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const crypto = cryptoInput.value.trim().toUpperCase();
                if (crypto) {
                    analyzeCrypto(crypto);
                }
            }
        });
    }

    // Quick crypto buttons
    quickCryptos.forEach(btn => {
        btn.addEventListener('click', () => {
            const crypto = btn.getAttribute('data-crypto');
            cryptoInput.value = crypto;
            analyzeCrypto(crypto);
        });
    });

    // Timeframe buttons
    cryptoTimeframeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            cryptoTimeframeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Refresh chart with new timeframe
            const period = btn.getAttribute('data-period');
            if (currentCrypto) {
                loadCryptoChartData(currentCrypto, period);
            }
        });
    });
}

/**
 * Analyze Cryptocurrency - Main Function
 */
async function analyzeCrypto(crypto) {
    if (isAnalyzingCrypto) return;
    
    console.log(`Analyzing crypto ${crypto}...`);
    isAnalyzingCrypto = true;
    currentCrypto = crypto;
    
    // Update UI state
    showCryptoLoadingState();
    
    try {
        // Fetch crypto predictions from backend
        const response = await fetch(`/api/crypto/predict/${crypto}`);
        
        if (!response.ok) {
            throw new Error(`Crypto API Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Crypto analysis successful:', data);
        
        // Update UI with real crypto data
        updateCryptoPredictionDisplay(data);
        updateCryptoUpdates(`🪙 Analysis complete for ${crypto}`);
        
        // Load crypto chart data
        await loadCryptoChartData(crypto);
        
        // Show crypto sections
        showCryptoResultSections();
        
    } catch (error) {
        console.error('Crypto analysis error:', error);
        showCryptoError(`Failed to analyze ${crypto}: ${error.message}`);
        updateCryptoUpdates(`❌ Error analyzing ${crypto}: ${error.message}`);
    } finally {
        hideCryptoLoadingState();
        isAnalyzingCrypto = false;
    }
}

/**
 * Update Crypto Prediction Display with Real Data
 */
function updateCryptoPredictionDisplay(data) {
    console.log('Updating crypto prediction display:', data);
    
    // Update current crypto price
    const currentPrice = data.current_price || data.price;
    if (currentPrice) {
        document.getElementById('currentCryptoPrice').textContent = `$${currentPrice.toFixed(2)}`;
    }
    
    // Update timestamp
    const timestamp = data.timestamp || new Date().toISOString();
    document.getElementById('cryptoPriceTimestamp').textContent = `Last updated: ${new Date(timestamp).toLocaleString()}`;
    
    // Update 24h change if available
    if (data.change_24h !== undefined) {
        const change = data.change_24h;
        const changePercent = data.change_percent_24h || 0;
        
        document.getElementById('cryptoChange').textContent = `$${change.toFixed(2)}`;
        document.getElementById('cryptoChangePercent').textContent = `${changePercent.toFixed(2)}%`;
        
        // Color coding
        const changeClass = change >= 0 ? 'text-success' : 'text-danger';
        document.getElementById('cryptoChange').className = `h4 ${changeClass}`;
        document.getElementById('cryptoChangePercent').className = `h6 ${changeClass}`;
    }
    
    // Update individual predictions
    const predictions = data.predictions || {};
    
    // Random Forest (Crypto)
    if (predictions.random_forest && !predictions.random_forest.error) {
        const rfPred = predictions.random_forest.prediction;
        const rfConf = (predictions.random_forest.confidence * 100) || 0;
        document.getElementById('cryptoRfPrediction').textContent = `$${rfPred.toFixed(2)}`;
        document.getElementById('cryptoRfConfidence').style.width = `${rfConf}%`;
        document.getElementById('cryptoRfConfidenceText').textContent = `${rfConf.toFixed(1)}% Confidence`;
        document.getElementById('cryptoRfCard').classList.add('active');
    } else {
        document.getElementById('cryptoRfPrediction').textContent = 'Error';
        document.getElementById('cryptoRfConfidenceText').textContent = 'Model Failed';
        document.getElementById('cryptoRfCard').classList.remove('active');
    }
    
    // XGBoost (Crypto)
    if (predictions.xgboost && !predictions.xgboost.error) {
        const xgbPred = predictions.xgboost.prediction;
        const xgbConf = (predictions.xgboost.confidence * 100) || 0;
        document.getElementById('cryptoXgbPrediction').textContent = `$${xgbPred.toFixed(2)}`;
        document.getElementById('cryptoXgbConfidence').style.width = `${xgbConf}%`;
        document.getElementById('cryptoXgbConfidenceText').textContent = `${xgbConf.toFixed(1)}% Confidence`;
        document.getElementById('cryptoXgbCard').classList.add('active');
    } else {
        document.getElementById('cryptoXgbPrediction').textContent = 'Error';
        document.getElementById('cryptoXgbConfidenceText').textContent = 'Model Failed';
        document.getElementById('cryptoXgbCard').classList.remove('active');
    }
    
    // Ensemble (Crypto)
    if (predictions.ensemble) {
        const ensemblePred = predictions.ensemble.prediction;
        const ensembleConf = (predictions.ensemble.confidence * 100) || 0;
        document.getElementById('cryptoEnsemblePrediction').textContent = `$${ensemblePred.toFixed(2)}`;
        document.getElementById('cryptoEnsembleConfidence').style.width = `${ensembleConf}%`;
        document.getElementById('cryptoEnsembleConfidenceText').textContent = `${ensembleConf.toFixed(1)}% Confidence`;
    }
    
    // Update market data if available
    if (data.market_data) {
        updateCryptoMarketData(data.market_data);
    }
    
    // Update sentiment data if available
    if (data.sentiment) {
        updateCryptoSentiment(data.sentiment);
    }
}

/**
 * Update Crypto Market Data
 */
function updateCryptoMarketData(marketData) {
    console.log('Updating crypto market data:', marketData);
    
    if (marketData.market_cap) {
        document.getElementById('marketCap').textContent = formatCurrency(marketData.market_cap);
    }
    
    if (marketData.volume_24h) {
        document.getElementById('volume24h').textContent = formatCurrency(marketData.volume_24h);
    }
    
    if (marketData.circulating_supply) {
        document.getElementById('circulatingSupply').textContent = formatNumber(marketData.circulating_supply);
    }
    
    if (marketData.market_rank) {
        document.getElementById('marketRank').textContent = `#${marketData.market_rank}`;
    }
}

/**
 * Update Crypto Sentiment Analysis
 */
function updateCryptoSentiment(sentiment) {
    console.log('Updating crypto sentiment:', sentiment);
    
    // Fear & Greed Index
    if (sentiment.fear_greed_index !== undefined) {
        const fgIndex = sentiment.fear_greed_index;
        const fgElement = document.getElementById('fearGreedIndex');
        fgElement.textContent = fgIndex;
        
        // Color coding based on value
        if (fgIndex < 25) {
            fgElement.className = 'sentiment-negative';
        } else if (fgIndex > 75) {
            fgElement.className = 'sentiment-positive';
        } else {
            fgElement.className = 'sentiment-neutral';
        }
    }
    
    // Social sentiment
    if (sentiment.social_sentiment) {
        const socialElement = document.getElementById('socialSentiment');
        socialElement.textContent = sentiment.social_sentiment;
        socialElement.className = getSentimentClass(sentiment.social_sentiment);
    }
    
    // News sentiment
    if (sentiment.news_sentiment) {
        const newsElement = document.getElementById('newsSentiment');
        newsElement.textContent = sentiment.news_sentiment;
        newsElement.className = getSentimentClass(sentiment.news_sentiment);
    }
    
    // Overall score
    if (sentiment.overall_score !== undefined) {
        const overallElement = document.getElementById('overallSentiment');
        overallElement.textContent = `${sentiment.overall_score}/100`;
        
        if (sentiment.overall_score < 40) {
            overallElement.className = 'sentiment-negative';
        } else if (sentiment.overall_score > 60) {
            overallElement.className = 'sentiment-positive';
        } else {
            overallElement.className = 'sentiment-neutral';
        }
    }
}

/**
 * Load Crypto Chart Data
 */
async function loadCryptoChartData(crypto, period = '1mo') {
    try {
        const response = await fetch(`/api/crypto/chart_data/${crypto}?period=${period}`);
        if (!response.ok) throw new Error('Crypto chart data fetch failed');
        
        const data = await response.json();
        updateCryptoChart(data);
        
    } catch (error) {
        console.error('Crypto chart data error:', error);
    }
}

/**
 * Initialize Crypto Chart
 */
function initializeCryptoChart() {
    const ctx = document.getElementById('cryptoChart');
    if (!ctx) {
        console.warn('Crypto chart canvas not found');
        return;
    }
    
    // Similar configuration to main chart but for crypto
    const config = {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Price',
                    data: [],
                    borderColor: 'rgba(255, 193, 7, 1)', // Gold for crypto
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'Crypto RF Prediction',
                    data: [],
                    borderColor: 'rgba(220, 53, 69, 0.8)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Crypto XGB Prediction',
                    data: [],
                    borderColor: 'rgba(25, 135, 84, 0.8)',
                    borderWidth: 2,
                    borderDash: [10, 5],
                    fill: false,
                    pointRadius: 0
                },
                {
                    label: 'Crypto Ensemble',
                    data: [],
                    borderColor: 'rgba(13, 202, 240, 1)',
                    backgroundColor: 'rgba(13, 202, 240, 0.2)',
                    borderWidth: 3,
                    fill: false,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#ffffff',
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(18, 18, 18, 0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff'
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8e9297' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    ticks: { 
                        color: '#8e9297',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    };
    
    try {
        cryptoChart = new Chart(ctx, config);
        console.log('Crypto chart initialized');
    } catch (error) {
        console.error('Crypto chart initialization error:', error);
    }
}

/**
 * Update Crypto Chart
 */
function updateCryptoChart(data) {
    if (!cryptoChart) return;
    
    try {
        console.log('Updating crypto chart:', data);
        
        // Clear existing data
        cryptoChart.data.labels = [];
        cryptoChart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        
        // Update historical price data
        if (data.labels && data.prices) {
            cryptoChart.data.labels = data.labels;
            cryptoChart.data.datasets[0].data = data.prices.map((price, index) => ({
                x: index,
                y: price
            }));
        }
        
        // Add prediction points if available
        if (data.predictions) {
            const lastIndex = data.labels ? data.labels.length - 1 : 0;
            const nextIndex = lastIndex + 1;
            
            if (data.predictions.random_forest && !data.predictions.random_forest.error) {
                cryptoChart.data.datasets[1].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.random_forest.prediction }
                ];
            }
            
            if (data.predictions.xgboost && !data.predictions.xgboost.error) {
                cryptoChart.data.datasets[2].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.xgboost.prediction }
                ];
            }
            
            if (data.predictions.ensemble) {
                cryptoChart.data.datasets[3].data = [
                    { x: lastIndex, y: data.prices[lastIndex] },
                    { x: nextIndex, y: data.predictions.ensemble.prediction }
                ];
            }
        }
        
        cryptoChart.update('none');
        
    } catch (error) {
        console.error('Crypto chart update error:', error);
    }
}

/**
 * Show/Hide Crypto UI Sections
 */
function showCryptoResultSections() {
    document.getElementById('cryptoPriceSection').style.display = 'block';
    document.getElementById('cryptoPredictionsSection').style.display = 'block';
    document.getElementById('cryptoChartSection').style.display = 'block';
}

function showCryptoLoadingState() {
    const analyzeBtn = document.getElementById('analyzeCryptoBtn');
    const analyzeText = document.getElementById('analyzeText');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (analyzeText) analyzeText.textContent = 'Analyzing...';
    if (loadingOverlay) loadingOverlay.style.display = 'flex';
}

function hideCryptoLoadingState() {
    const analyzeBtn = document.getElementById('analyzeCryptoBtn');
    const analyzeText = document.getElementById('analyzeText');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (analyzeText) analyzeText.textContent = 'Analyze';
    if (loadingOverlay) loadingOverlay.style.display = 'none';
}

function showCryptoError(message) {
    createToast(message, 'error');
}

/**
 * Update Crypto Updates Feed
 */
function updateCryptoUpdates(message) {
    const updatesContainer = document.getElementById('cryptoUpdates');
    if (!updatesContainer) return;
    
    const timestamp = new Date().toLocaleTimeString();
    
    const updateElement = document.createElement('div');
    updateElement.className = 'mb-2 p-2 rounded glass-effect fade-in';
    updateElement.innerHTML = `
        <small class="text-muted">${timestamp}</small><br>
        ${message}
    `;
    
    updatesContainer.insertBefore(updateElement, updatesContainer.firstChild);
    
    // Keep only last 10 updates
    while (updatesContainer.children.length > 10) {
        updatesContainer.removeChild(updatesContainer.lastChild);
    }
}

/**
 * Utility Functions
 */
function formatCurrency(value) {
    if (value >= 1e12) {
        return '$' + (value / 1e12).toFixed(2) + 'T';
    } else if (value >= 1e9) {
        return '$' + (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return '$' + (value / 1e6).toFixed(2) + 'M';
    } else if (value >= 1e3) {
        return '$' + (value / 1e3).toFixed(2) + 'K';
    } else {
        return '$' + value.toFixed(2);
    }
}

function formatNumber(value) {
    if (value >= 1e9) {
        return (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return (value / 1e6).toFixed(2) + 'M';
    } else if (value >= 1e3) {
        return (value / 1e3).toFixed(2) + 'K';
    } else {
        return value.toLocaleString();
    }
}

function getSentimentClass(sentiment) {
    const lower = sentiment.toLowerCase();
    if (lower.includes('positive') || lower.includes('bullish')) {
        return 'sentiment-positive';
    } else if (lower.includes('negative') || lower.includes('bearish')) {
        return 'sentiment-negative';
    } else {
        return 'sentiment-neutral';
    }
}

// Export functions for global access
window.analyzeCrypto = analyzeCrypto;
window.initializeCryptoDashboard = initializeCryptoDashboard;
