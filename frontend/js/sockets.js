/**
 * FullStock AI WebSocket Client - Real-time Data Streaming
 * Handles live price updates, predictions, and system notifications
 */

let socket = null;
let connectionRetryCount = 0;
const maxRetryAttempts = 5;
let reconnectInterval = null;

/**
 * Initialize WebSocket Connection
 */
function initializeWebSocket() {
    try {
        // Connect to Socket.IO server with more conservative settings
        socket = io({
            transports: ['polling', 'websocket'], // Try polling first, then websocket
            upgrade: true,
            forceNew: false,
            timeout: 15000,
            reconnection: true,
            reconnectionDelay: 2000,
            reconnectionDelayMax: 10000,
            reconnectionAttempts: 5,
            maxReconnectionAttempts: 5,
            pingTimeout: 30000,
            pingInterval: 15000
        });
        
        setupSocketEventListeners();
        console.log('WebSocket connection initiated');
        
    } catch (error) {
        console.error('WebSocket initialization error:', error);
        updateConnectionStatus('warning', 'HTTP Mode');
        // Gracefully degrade to HTTP-only mode
        fallbackToHttpMode();
    }
}

/**
 * Setup Socket Event Listeners
 */
function setupSocketEventListeners() {
    // Connection established
    socket.on('connect', () => {
        console.log('WebSocket connected');
        connectionRetryCount = 0;
        updateConnectionStatus('online', 'Live');
        
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
        
        // Request initial data if ticker is set
        if (window.currentTicker) {
            requestLiveData(window.currentTicker);
        }
        
        // Update live feed
        if (typeof updateLiveUpdates === 'function') {
            updateLiveUpdates('🟢 Connected to live data stream');
        }
    });
    
    // Connection lost
    socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        updateConnectionStatus('warning', 'Reconnecting...');
        
        if (typeof updateLiveUpdates === 'function') {
            updateLiveUpdates('🟡 Connection lost, attempting to reconnect...');
        }
        
        // Auto-reconnect logic
        if (reason === 'io server disconnect') {
            // Server initiated disconnect, reconnect manually
            setTimeout(() => socket.connect(), 2000);
        }
    });
    
    // Connection error
    socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        connectionRetryCount++;
        
        if (connectionRetryCount <= maxRetryAttempts) {
            updateConnectionStatus('warning', `Retry ${connectionRetryCount}/${maxRetryAttempts}`);
            // Don't retry too aggressively - let Socket.IO handle it
        } else {
            updateConnectionStatus('error', 'Offline');
            if (typeof updateLiveUpdates === 'function') {
                updateLiveUpdates('🔴 WebSocket failed, using HTTP mode');
            }
            // Fall back to HTTP polling
            fallbackToHttpMode();
        }
    });
    
    // Real-time price updates
    socket.on('price_update', (data) => {
        console.log('Received price update:', data);
        handlePriceUpdate(data);
    });
    
    // ML prediction updates
    socket.on('prediction_update', (data) => {
        console.log('Received prediction update:', data);
        handlePredictionUpdate(data);
    });
    
    // System notifications
    socket.on('system_notification', (data) => {
        console.log('System notification:', data);
        handleSystemNotification(data);
    });
    
    // Model status updates
    socket.on('model_status', (data) => {
        console.log('Model status update:', data);
        handleModelStatusUpdate(data);
    });
    
    // Oracle insights (if available)
    socket.on('oracle_insight', (data) => {
        console.log('Oracle insight received:', data);
        handleOracleInsight(data);
    });
    
    // Market alerts
    socket.on('market_alert', (data) => {
        console.log('Market alert:', data);
        handleMarketAlert(data);
    });
}

/**
 * Handle Real-time Price Updates
 */
function handlePriceUpdate(data) {
    if (data.ticker === window.currentTicker) {
        // Update current price display
        const priceElement = document.getElementById('currentPrice');
        if (priceElement && data.price) {
            priceElement.textContent = `$${data.price.toFixed(2)}`;
            
            // Add visual feedback for price changes
            priceElement.classList.add('text-success');
            setTimeout(() => {
                priceElement.classList.remove('text-success');
            }, 1000);
        }
        
        // Update timestamp
        const timestampElement = document.getElementById('priceTimestamp');
        if (timestampElement) {
            timestampElement.textContent = `Last updated: ${new Date().toLocaleString()}`;
        }
        
        // Update live feed
        if (typeof updateLiveUpdates === 'function') {
            updateLiveUpdates(`📈 ${data.ticker}: $${data.price.toFixed(2)} ${data.change > 0 ? '↗️' : '↘️'}`);
        }
    }
}

/**
 * Handle Prediction Updates
 */
function handlePredictionUpdate(data) {
    if (data.ticker === window.currentTicker) {
        console.log('Updating predictions from WebSocket:', data);
        
        // Update prediction display if function exists
        if (typeof updatePredictionDisplay === 'function') {
            updatePredictionDisplay(data);
        }
        
        // Update live feed
        if (typeof updateLiveUpdates === 'function') {
            const ensemblePrice = data.predictions?.ensemble?.prediction;
            if (ensemblePrice) {
                updateLiveUpdates(`🤖 New prediction for ${data.ticker}: $${ensemblePrice.toFixed(2)}`);
            }
        }
    }
}

/**
 * Handle System Notifications
 */
function handleSystemNotification(data) {
    console.log('System notification:', data);
    
    // Update live feed
    if (typeof updateLiveUpdates === 'function') {
        const icon = data.type === 'error' ? '🔴' : data.type === 'warning' ? '🟡' : '🟢';
        updateLiveUpdates(`${icon} ${data.message}`);
    }
    
    // Show toast notification if available
    if (typeof showNotification === 'function') {
        showNotification(data.message, data.type);
    }
}

/**
 * Handle Model Status Updates
 */
function handleModelStatusUpdate(data) {
    console.log('Model status update:', data);
    
    // Update model status indicators
    const models = ['rf', 'lstm', 'xgb'];
    models.forEach(model => {
        const statusElement = document.getElementById(`${model}Status`);
        if (statusElement && data[model]) {
            statusElement.className = `status-indicator ${getStatusClass(data[model].status)}`;
        }
    });
    
    // Update live feed
    if (typeof updateLiveUpdates === 'function') {
        updateLiveUpdates(`⚙️ Model health check: ${data.healthy_models || 0}/3 models operational`);
    }
}

/**
 * Handle Oracle Insights
 */
function handleOracleInsight(data) {
    console.log('Oracle insight:', data);
    
    // Update oracle panel if on oracle page
    if (typeof updateOraclePanel === 'function') {
        updateOraclePanel(data);
    }
    
    // Update live feed
    if (typeof updateLiveUpdates === 'function') {
        updateLiveUpdates(`🔮 Oracle insight: ${data.symbol || 'Mystical guidance received'}`);
    }
}

/**
 * Handle Market Alerts
 */
function handleMarketAlert(data) {
    console.log('Market alert:', data);
    
    // Update live feed with alert
    if (typeof updateLiveUpdates === 'function') {
        const alertIcon = data.severity === 'high' ? '🚨' : data.severity === 'medium' ? '⚠️' : 'ℹ️';
        updateLiveUpdates(`${alertIcon} Alert: ${data.message}`);
    }
    
    // Show prominent notification for high severity
    if (data.severity === 'high' && typeof showNotification === 'function') {
        showNotification(data.message, 'warning');
    }
}

/**
 * Request Live Data for Ticker
 */
function requestLiveData(ticker) {
    if (socket && socket.connected) {
        console.log(`Requesting live data for ${ticker}`);
        socket.emit('subscribe_ticker', { ticker: ticker });
        
        // Request initial prediction update
        socket.emit('request_prediction', { ticker: ticker });
    }
}

/**
 * Unsubscribe from Ticker Updates
 */
function unsubscribeTicker(ticker) {
    if (socket && socket.connected) {
        socket.emit('unsubscribe_ticker', { ticker: ticker });
    }
}

/**
 * Update Connection Status UI
 */
function updateConnectionStatus(status, text) {
    const statusElement = document.getElementById('connectionStatus');
    const textElement = document.getElementById('connectionText');
    
    if (statusElement) {
        statusElement.className = `status-indicator ${getStatusClass(status)}`;
    }
    
    if (textElement) {
        textElement.textContent = text;
    }
}

/**
 * Get Status CSS Class
 */
function getStatusClass(status) {
    switch (status) {
        case 'online':
        case 'healthy':
        case 'operational':
            return 'status-online';
        case 'warning':
        case 'degraded':
            return 'status-warning';
        case 'error':
        case 'offline':
        case 'failed':
            return 'status-error';
        default:
            return 'status-warning';
    }
}

/**
 * Send Custom Message
 */
function sendSocketMessage(event, data) {
    if (socket && socket.connected) {
        socket.emit(event, data);
        return true;
    }
    return false;
}

/**
 * Cleanup WebSocket Connection
 */
function cleanupWebSocket() {
    if (socket) {
        socket.disconnect();
        socket = null;
    }
    
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
}

/**
 * Fallback to HTTP-only mode when WebSocket fails
 */
function fallbackToHttpMode() {
    console.log('Falling back to HTTP-only mode');
    updateConnectionStatus('warning', 'HTTP Only');
    
    // Disable socket-based features
    if (socket) {
        socket.disconnect();
        socket = null;
    }
    
    // Clear any retry intervals
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
    
    // Don't start polling immediately - let user-initiated requests handle updates
    if (typeof updateLiveUpdates === 'function') {
        updateLiveUpdates('📡 Using HTTP mode for data updates');
    }
}

/**
 * Fetch prediction update via HTTP when WebSocket unavailable
 */
async function fetchPredictionUpdate(ticker) {
    try {
        const response = await fetch(`/api/predict/${ticker}`);
        const data = await response.json();
        if (data && !data.error) {
            handlePredictionUpdate(data);
            if (typeof updateLiveUpdates === 'function') {
                updateLiveUpdates(`📊 Updated ${ticker} via HTTP: $${data.current_price.toFixed(2)}`);
            }
        }
    } catch (error) {
        console.error('HTTP prediction update failed:', error);
    }
}

// Export functions for global access
window.initializeWebSocket = initializeWebSocket;
window.requestLiveData = requestLiveData;
window.unsubscribeTicker = unsubscribeTicker;
window.sendSocketMessage = sendSocketMessage;
window.cleanupWebSocket = cleanupWebSocket;
window.fallbackToHttpMode = fallbackToHttpMode;

// Cleanup on page unload
window.addEventListener('beforeunload', cleanupWebSocket);