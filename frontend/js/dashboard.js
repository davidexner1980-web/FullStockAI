/**
 * FullStock AI Dashboard - Real Data Integration
 * Handles stock analysis, predictions display, and live updates
 */

let currentTicker = 'SPY';
let isAnalyzing = false;

/**
 * Initialize Dashboard
 */
function initializeDashboard() {
    console.log('FullStock AI vNext Ultimate initialized');
    
    // Force hide any existing loading overlay
    forceHideLoading();
    
    // Setup event listeners
    setupEventListeners();

    // Scroll to top button
    setupScrollTopButton();
    
    // Initialize WebSocket connection
    if (typeof initializeWebSocket === 'function') {
        initializeWebSocket();
    }
    
    // Setup chart
    if (typeof initializeChart === 'function') {
        initializeChart();
    }
    
    console.log('Dashboard initialized successfully');
}

/**
 * Force hide loading overlay - failsafe function
 */
function forceHideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
        loadingOverlay.style.visibility = 'hidden';
        console.log('Loading overlay force hidden');
    }
    
    // Clear any stuck intervals
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
        window.loadingInterval = null;
    }
    
    // Reset analyze button
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeText = document.getElementById('analyzeText');
    const analyzeSpinner = document.getElementById('analyzeSpinner');
    if (analyzeBtn) analyzeBtn.disabled = false;
    if (analyzeText) analyzeText.textContent = 'Analyze';
    if (analyzeSpinner) analyzeSpinner.style.display = 'none';
    
    // Reset analyzing flag
    isAnalyzing = false;
    
    console.log('Force loading reset complete');
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const tickerInput = document.getElementById('tickerInput');
    const quickTickers = document.querySelectorAll('.quick-ticker');
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');

    // Analyze button
    analyzeBtn.addEventListener('click', () => {
        const ticker = tickerInput.value.trim().toUpperCase();
        if (ticker) {
            analyzeStock(ticker);
        }
    });

    // Enter key in input
    tickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const ticker = tickerInput.value.trim().toUpperCase();
            if (ticker) {
                analyzeStock(ticker);
            }
        }
    });

    // Quick ticker buttons
    quickTickers.forEach(btn => {
        btn.addEventListener('click', () => {
            const ticker = btn.getAttribute('data-ticker');
            tickerInput.value = ticker;
            analyzeStock(ticker);
        });
    });

    // Timeframe buttons
    timeframeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            timeframeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Refresh chart with new timeframe
            const period = btn.getAttribute('data-period');
            if (currentTicker) {
                loadChartData(currentTicker, period);
            }
        });
    });
}

/**
 * Setup Scroll to Top button
 */
function setupScrollTopButton() {
    const scrollBtn = document.getElementById('scrollTopBtn');
    if (!scrollBtn) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 200) {
            scrollBtn.style.display = 'flex';
        } else {
            scrollBtn.style.display = 'none';
        }
    });

    scrollBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/**
 * Analyze Stock - Main Function
 */
async function analyzeStock(ticker) {
    if (isAnalyzing) return;
    
    console.log(`Analyzing ${ticker}...`);
    isAnalyzing = true;
    currentTicker = ticker;
    
    // Update UI state
    showLoadingState();
    
    try {
        // Fetch predictions from backend
        const response = await fetch(`/api/predict/${ticker}`);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Analysis successful, updating UI...', data);
        
        // Update UI with real data
        updatePredictionDisplay(data);
        updateLiveUpdates(`📊 Analysis complete for ${ticker}`);
        
        // Load chart data
        await loadChartData(ticker);
        
        // Show sections
        showResultSections();
        console.log('Result sections shown, analysis complete');
        
    } catch (error) {
        console.error('Analysis error:', error);
        showError(`Failed to analyze ${ticker}: ${error.message}`);
        updateLiveUpdates(`❌ Error analyzing ${ticker}: ${error.message}`);
    } finally {
        console.log('Analysis completed, hiding loading state...');
        // Force hide loading immediately
        hideLoadingState();
        // Also try after a short delay as backup
        setTimeout(() => {
            hideLoadingState();
            console.log('Analysis fully completed with backup hide');
        }, 500);
    }
}

/**
 * Update Prediction Display with Real Data
 */
function updatePredictionDisplay(data) {
    console.log('Updating prediction display with data:', data);
    
    // Update current price
    const currentPrice = data.current_price;
    console.log('Setting current price:', currentPrice);
    document.getElementById('currentPrice').textContent = `$${currentPrice.toFixed(2)}`;
    console.log('Current price element text now:', document.getElementById('currentPrice').textContent);
    
    // Update timestamp
    document.getElementById('priceTimestamp').textContent = `Last updated: ${new Date(data.timestamp).toLocaleString()}`;
    
    // Update individual predictions
    const predictions = data.predictions;
    console.log('Updating individual predictions:', predictions);
    
    // Random Forest
    if (predictions.random_forest && predictions.random_forest.prediction !== undefined && !predictions.random_forest.error) {
        const rfPred = predictions.random_forest.prediction;
        const rfConf = (predictions.random_forest.confidence * 100) || 0;
        console.log('Setting RF prediction:', rfPred);
        document.getElementById('rfPrediction').textContent = `$${rfPred.toFixed(2)}`;
        console.log('RF element text now:', document.getElementById('rfPrediction').textContent);
        document.getElementById('rfConfidence').style.width = `${rfConf}%`;
        document.getElementById('rfConfidenceText').textContent = `${rfConf.toFixed(1)}% Confidence`;
        document.getElementById('randomForestCard').classList.add('active');
    } else {
        document.getElementById('rfPrediction').textContent = 'Error';
        document.getElementById('rfConfidenceText').textContent = 'Model Failed';
        document.getElementById('randomForestCard').classList.remove('active');
    }
    
    // LSTM
    if (predictions.lstm && predictions.lstm.prediction !== undefined && !predictions.lstm.error) {
        const lstmPred = predictions.lstm.prediction;
        const lstmConf = (predictions.lstm.confidence * 100) || 0;
        document.getElementById('lstmPrediction').textContent = `$${lstmPred.toFixed(2)}`;
        document.getElementById('lstmConfidence').style.width = `${lstmConf}%`;
        document.getElementById('lstmConfidenceText').textContent = `${lstmConf.toFixed(1)}% Confidence`;
        document.getElementById('lstmCard').classList.add('active');
        document.getElementById('lstmStatus').className = 'status-indicator status-online';
    } else {
        document.getElementById('lstmPrediction').textContent = 'Error';
        document.getElementById('lstmConfidenceText').textContent = 'TensorFlow Issue';
        document.getElementById('lstmCard').classList.remove('active');
        document.getElementById('lstmStatus').className = 'status-indicator status-warning';
    }
    
    // XGBoost
    if (predictions.xgboost && predictions.xgboost.prediction !== undefined && !predictions.xgboost.error) {
        const xgbPred = predictions.xgboost.prediction;
        const xgbConf = (predictions.xgboost.confidence * 100) || 0;
        document.getElementById('xgbPrediction').textContent = `$${xgbPred.toFixed(2)}`;
        document.getElementById('xgbConfidence').style.width = `${xgbConf}%`;
        document.getElementById('xgbConfidenceText').textContent = `${xgbConf.toFixed(1)}% Confidence`;
        document.getElementById('xgboostCard').classList.add('active');
    } else {
        document.getElementById('xgbPrediction').textContent = 'Error';
        document.getElementById('xgbConfidenceText').textContent = 'Model Failed';
        document.getElementById('xgboostCard').classList.remove('active');
    }
    
    // Ensemble
    if (predictions.ensemble && predictions.ensemble.prediction !== undefined) {
        const ensemblePred = predictions.ensemble.prediction;
        const ensembleConf = (predictions.ensemble.confidence * 100) || 0;
        console.log('Updating ensemble prediction:', ensemblePred, ensembleConf);
        document.getElementById('ensemblePrediction').textContent = `$${ensemblePred.toFixed(2)}`;
        document.getElementById('ensembleConfidence').style.width = `${ensembleConf}%`;
        document.getElementById('ensembleConfidenceText').textContent = `${ensembleConf.toFixed(1)}% Confidence`;
    }
    
    // Update agreement level
    const agreementPercent = ((data.agreement_level || 0) * 100).toFixed(1);
    document.getElementById('agreementLevel').textContent = `${agreementPercent}%`;
}

/**
 * Load Chart Data
 */
async function loadChartData(ticker, period = '1mo') {
    try {
        const response = await fetch(`/api/history/${ticker}?period=${period}`);
        if (!response.ok) throw new Error('Chart data fetch failed');
        
        const data = await response.json();
        console.log('Updating chart with data:', data);
        updateChart(data);
        console.log('Chart updated successfully');
        
    } catch (error) {
        console.error('Chart data error:', error);
    }
}

/**
 * Show/Hide UI Sections
 */
function showResultSections() {
    console.log('Showing results section');
    document.getElementById('priceSection').style.display = 'block';
    document.getElementById('predictionsSection').style.display = 'block';
    document.getElementById('chartSection').style.display = 'block';
    document.getElementById('analysisSection').style.display = 'block';
    console.log('Results section is now visible');
}

function showLoadingState() {
    console.log('Showing loading state...');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeText = document.getElementById('analyzeText');
    const analyzeSpinner = document.getElementById('analyzeSpinner');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        console.log('Analyze button disabled');
    }
    if (analyzeText) {
        analyzeText.textContent = 'Analyzing...';
        console.log('Analyze text updated');
    }
    if (analyzeSpinner) {
        analyzeSpinner.style.display = 'inline-block';
        console.log('Analyze spinner shown');
    }
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
        console.log('Loading overlay shown');
    }
    
    // Update loading text periodically
    const messages = [
        'Fetching real-time prices...',
        'Running ML predictions...',
        'Analyzing market trends...',
        'Processing ensemble results...'
    ];
    let msgIndex = 0;
    const loadingInterval = setInterval(() => {
        document.getElementById('loadingText').textContent = messages[msgIndex];
        msgIndex = (msgIndex + 1) % messages.length;
    }, 1500);
    
    // Store interval for cleanup
    window.loadingInterval = loadingInterval;
}

function hideLoadingState() {
    console.log('Hiding loading state...');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeText = document.getElementById('analyzeText');
    const analyzeSpinner = document.getElementById('analyzeSpinner');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
        console.log('Analyze button enabled');
    }
    if (analyzeText) {
        analyzeText.textContent = 'Analyze';
        console.log('Analyze text reset');
    }
    if (analyzeSpinner) {
        analyzeSpinner.style.display = 'none';
        console.log('Analyze spinner hidden');
    }
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
        loadingOverlay.style.visibility = 'hidden'; // Extra enforcement
        console.log('Loading overlay hidden');
    }
    
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
        window.loadingInterval = null;
        console.log('Loading interval cleared');
    }
    
    // Force flag reset
    isAnalyzing = false;
    
    console.log('Loading state hidden successfully');
}

/**
 * Show Error Message
 */
function showError(message) {
    // You could implement a toast notification system here
    console.error(message);
}

/**
 * Update Live Updates Feed
 */
function updateLiveUpdates(message) {
    const updatesContainer = document.getElementById('liveUpdates');
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
 * Mobile Touch Handlers
 */
function setupMobileHandlers() {
    // Swipe handlers for mobile charts
    let startX = 0;
    let startY = 0;
    
    const chartContainer = document.querySelector('.chart-container');
    if (chartContainer) {
        chartContainer.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        chartContainer.addEventListener('touchend', (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Horizontal swipe
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 100) {
                const timeframeBtns = document.querySelectorAll('.timeframe-btn');
                const activeBtn = document.querySelector('.timeframe-btn.active');
                const activeBtnIndex = Array.from(timeframeBtns).indexOf(activeBtn);
                
                if (diffX > 0 && activeBtnIndex < timeframeBtns.length - 1) {
                    // Swipe left - next timeframe
                    timeframeBtns[activeBtnIndex + 1].click();
                } else if (diffX < 0 && activeBtnIndex > 0) {
                    // Swipe right - previous timeframe
                    timeframeBtns[activeBtnIndex - 1].click();
                }
            }
        });
    }
}

// Initialize mobile handlers after DOM load
document.addEventListener('DOMContentLoaded', setupMobileHandlers);

// Export functions for global access
window.analyzeStock = analyzeStock;
window.initializeDashboard = initializeDashboard;