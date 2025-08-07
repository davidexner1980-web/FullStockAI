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
    
    // Setup event listeners
    setupEventListeners();
    
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
 * Analyze Stock - Main Function
 */
async function analyzeStock(ticker) {
    if (isAnalyzing) return;
    
    console.log(`Analyzing ${ticker}...`);
    isAnalyzing = true;
    currentTicker = ticker;
    
    // Update UI state
    showLoadingState();
    
    // Set up a safety timeout to ensure loading state gets cleared
    const timeoutId = setTimeout(() => {
        console.warn('Analysis timeout reached, forcing cleanup');
        hideLoadingState();
        isAnalyzing = false;
        showError(`Analysis timeout for ${ticker} - please try again`);
        updateLiveUpdates(`⏰ Analysis timeout for ${ticker}`);
    }, 30000); // 30 second timeout
    
    try {
        // Fetch predictions from backend with timeout
        const controller = new AbortController();
        const timeoutSignal = setTimeout(() => controller.abort(), 25000); // 25s fetch timeout
        
        const response = await fetch(`/api/predict/${ticker}`, {
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        clearTimeout(timeoutSignal);
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status} - ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Validate response data
        if (!data || !data.current_price) {
            throw new Error('Invalid response data from API');
        }
        
        console.log('Analysis successful, updating UI...', data);
        
        // Update UI with real data
        updatePredictionDisplay(data);
        updateLiveUpdates(`📊 Analysis complete for ${ticker}`);
        
        // Load chart data
        try {
            await loadChartData(ticker);
        } catch (chartError) {
            console.warn('Chart loading failed:', chartError);
            updateLiveUpdates(`⚠️ Chart data unavailable for ${ticker}`);
        }
        
        // Show sections
        showResultSections();
        
        // Clear the timeout since we succeeded
        clearTimeout(timeoutId);
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        console.error('Analysis error:', error);
        
        let errorMessage = error.message;
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out - please try again';
        }
        
        showError(`Failed to analyze ${ticker}: ${errorMessage}`);
        updateLiveUpdates(`❌ Error analyzing ${ticker}: ${errorMessage}`);
        
        // Show a user-friendly error state
        showErrorState(ticker, errorMessage);
        
    } finally {
        hideLoadingState();
        isAnalyzing = false;
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
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeText = document.getElementById('analyzeText');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    analyzeBtn.disabled = true;
    analyzeText.textContent = 'Analyzing...';
    loadingOverlay.style.display = 'flex';
    
    // Clear any existing interval first
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
    }
    
    // Update loading text periodically
    const messages = [
        'Fetching real-time prices...',
        'Running ML predictions...',
        'Analyzing market trends...',
        'Processing ensemble results...',
        'Finalizing analysis...'
    ];
    let msgIndex = 0;
    
    // Set initial message
    const loadingTextElement = document.getElementById('loadingText');
    if (loadingTextElement) {
        loadingTextElement.textContent = messages[0];
    }
    
    // Create new interval
    const loadingInterval = setInterval(() => {
        if (loadingTextElement) {
            msgIndex = (msgIndex + 1) % messages.length;
            loadingTextElement.textContent = messages[msgIndex];
        }
    }, 2000);
    
    // Store interval for cleanup
    window.loadingInterval = loadingInterval;
}

function hideLoadingState() {
    console.log('Hiding loading state');
    
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analyzeText = document.getElementById('analyzeText');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    if (analyzeBtn) {
        analyzeBtn.disabled = false;
    }
    if (analyzeText) {
        analyzeText.textContent = 'Analyze';
    }
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
    
    // Always clear the loading interval
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
        window.loadingInterval = null;
    }
    
    console.log('Loading state hidden');
}

/**
 * Show Error Message
 */
function showError(message) {
    console.error(message);
    
    // Show error in live updates
    updateLiveUpdates(`🔴 ${message}`);
    
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = 'position-fixed top-0 end-0 p-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast show" role="alert">
            <div class="toast-header bg-danger text-white">
                <strong class="me-auto">Error</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}

/**
 * Show Error State in UI
 */
function showErrorState(ticker, message) {
    // Update price section with error
    const priceElement = document.getElementById('currentPrice');
    if (priceElement) {
        priceElement.textContent = 'Error';
        priceElement.className = 'display-4 fw-bold text-danger';
    }
    
    const timestampElement = document.getElementById('priceTimestamp');
    if (timestampElement) {
        timestampElement.textContent = `Failed to analyze ${ticker}: ${message}`;
    }
    
    // Show error message in results section
    document.getElementById('priceSection').style.display = 'block';
    
    // Reset prediction cards to error state
    const predictionCards = ['randomForestCard', 'lstmCard', 'xgboostCard'];
    predictionCards.forEach(cardId => {
        const card = document.getElementById(cardId);
        if (card) {
            card.classList.remove('active');
            const predictionElement = card.querySelector('[id$="Prediction"]');
            if (predictionElement) {
                predictionElement.textContent = 'Error';
            }
        }
    });
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

// Safety mechanism: Global click handler to clear stuck loading states
document.addEventListener('click', (e) => {
    // If clicking on the loading overlay itself, force clear it after 2 seconds
    if (e.target.closest('#loadingOverlay') && window.loadingInterval) {
        setTimeout(() => {
            if (document.getElementById('loadingOverlay').style.display !== 'none') {
                console.warn('Force clearing stuck loading state via click');
                hideLoadingState();
                isAnalyzing = false;
                updateLiveUpdates('⚠️ Loading state cleared manually');
            }
        }, 2000);
    }
});

// Safety backup: Clear any loading state that's been active too long
setInterval(() => {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay && loadingOverlay.style.display === 'flex') {
        // If loading has been showing for more than 45 seconds, force clear
        if (!window.loadingStartTime) {
            window.loadingStartTime = Date.now();
        } else if (Date.now() - window.loadingStartTime > 45000) {
            console.warn('Force clearing loading state - timeout exceeded');
            hideLoadingState();
            isAnalyzing = false;
            updateLiveUpdates('🕐 Analysis timeout - please try again');
            delete window.loadingStartTime;
        }
    } else {
        // Clear timestamp when not loading
        delete window.loadingStartTime;
    }
}, 5000); // Check every 5 seconds

// Initialize mobile handlers after DOM load
document.addEventListener('DOMContentLoaded', setupMobileHandlers);

// Export functions for global access
window.analyzeStock = analyzeStock;
window.initializeDashboard = initializeDashboard;