/**
 * WebSocketClient - Real-time data connection for FullStock AI
 */

class WebSocketClient {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000;
        this.heartbeatInterval = null;
        this.eventListeners = new Map();
        this.isConnected = false;
        this.subscriptions = new Set();
        this.messageQueue = [];
        
        this.init();
    }

    init() {
        console.log('WebSocketClient: Initializing...');
        this.connect();
    }

    connect() {
        try {
            // Use appropriate WebSocket URL based on environment
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('WebSocketClient: Connecting to', wsUrl);
            
            this.socket = new WebSocket(wsUrl);
            this.setupEventHandlers();
            
        } catch (error) {
            console.error('WebSocketClient: Connection failed', error);
            this.handleConnectionError(error);
        }
    }

    setupEventHandlers() {
        this.socket.onopen = (event) => {
            console.log('WebSocketClient: Connected successfully');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Start heartbeat
            this.startHeartbeat();
            
            // Process queued messages
            this.processMessageQueue();
            
            // Restore subscriptions
            this.restoreSubscriptions();
            
            // Notify listeners
            this.emit('connected', { timestamp: Date.now() });
            
            // Update UI connection status
            this.updateConnectionStatus('connected');
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocketClient: Message received', data.type);
                this.handleMessage(data);
            } catch (error) {
                console.error('WebSocketClient: Failed to parse message', error);
            }
        };

        this.socket.onclose = (event) => {
            console.log('WebSocketClient: Connection closed', event.code, event.reason);
            this.isConnected = false;
            this.stopHeartbeat();
            
            // Update UI connection status
            this.updateConnectionStatus('disconnected');
            
            // Notify listeners
            this.emit('disconnected', { 
                code: event.code, 
                reason: event.reason,
                timestamp: Date.now()
            });
            
            // Attempt reconnection if not intentional
            if (event.code !== 1000) {
                this.scheduleReconnect();
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocketClient: Connection error', error);
            this.emit('error', { error: error, timestamp: Date.now() });
            this.handleConnectionError(error);
        };
    }

    handleMessage(data) {
        const { type, payload } = data;
        
        switch (type) {
            case 'price_update':
                this.handlePriceUpdate(payload);
                break;
            case 'prediction_update':
                this.handlePredictionUpdate(payload);
                break;
            case 'market_alert':
                this.handleMarketAlert(payload);
                break;
            case 'portfolio_update':
                this.handlePortfolioUpdate(payload);
                break;
            case 'crypto_update':
                this.handleCryptoUpdate(payload);
                break;
            case 'heartbeat':
                this.handleHeartbeat(payload);
                break;
            case 'subscription_confirmed':
                this.handleSubscriptionConfirmed(payload);
                break;
            case 'error':
                this.handleServerError(payload);
                break;
            default:
                console.warn('WebSocketClient: Unknown message type', type);
        }
        
        // Emit to registered listeners
        this.emit(type, payload);
    }

    handlePriceUpdate(payload) {
        const { symbol, price, change, volume, timestamp } = payload;
        
        // Update price displays
        this.updatePriceDisplays(symbol, price, change);
        
        // Check for alerts
        this.checkPriceAlerts(symbol, price);
        
        // Update charts if visible
        this.updateCharts(symbol, price, timestamp);
        
        console.log(`Price update: ${symbol} = $${price} (${change > 0 ? '+' : ''}${change}%)`);
    }

    handlePredictionUpdate(payload) {
        const { symbol, prediction, confidence, model } = payload;
        
        // Update prediction displays
        this.updatePredictionDisplays(symbol, prediction, confidence, model);
        
        console.log(`Prediction update: ${symbol} -> $${prediction} (${confidence}% confidence)`);
    }

    handleMarketAlert(payload) {
        const { level, message, symbol, timestamp } = payload;
        
        // Show alert notification
        this.showAlertNotification(level, message, symbol);
        
        // Log to console
        console.log(`Market alert [${level}]: ${message}`);
        
        // Trigger haptic feedback on mobile
        if (window.MobileGestures) {
            const intensity = level === 'high' ? 'heavy' : level === 'medium' ? 'medium' : 'light';
            window.app?.mobileGestures?.triggerHaptic(intensity);
        }
    }

    handlePortfolioUpdate(payload) {
        const { totalValue, totalPnL, holdings } = payload;
        
        // Update portfolio displays
        if (window.portfolioManager) {
            window.portfolioManager.updateRealTimeData(payload);
        }
        
        console.log(`Portfolio update: Value = $${totalValue}, P&L = $${totalPnL}`);
    }

    handleCryptoUpdate(payload) {
        const { symbol, price, change, volume } = payload;
        
        // Update crypto displays
        if (window.cryptoTracker) {
            window.cryptoTracker.handlePriceUpdate(payload);
        }
        
        console.log(`Crypto update: ${symbol} = $${price} (${change > 0 ? '+' : ''}${change}%)`);
    }

    handleHeartbeat(payload) {
        // Respond to heartbeat
        this.send('heartbeat_response', { timestamp: Date.now() });
    }

    handleSubscriptionConfirmed(payload) {
        const { symbol, type } = payload;
        console.log(`Subscription confirmed: ${type} for ${symbol}`);
    }

    handleServerError(payload) {
        const { message, code } = payload;
        console.error(`Server error [${code}]: ${message}`);
        
        if (window.app) {
            window.app.showErrorMessage('Server Error', message);
        }
    }

    // Subscription management
    subscribe(type, symbol = null) {
        const subscription = { type, symbol, timestamp: Date.now() };
        this.subscriptions.add(JSON.stringify(subscription));
        
        if (this.isConnected) {
            this.send('subscribe', subscription);
        } else {
            console.log('WebSocketClient: Queued subscription', subscription);
        }
    }

    unsubscribe(type, symbol = null) {
        const subscription = { type, symbol };
        this.subscriptions.delete(JSON.stringify(subscription));
        
        if (this.isConnected) {
            this.send('unsubscribe', subscription);
        }
    }

    subscribeToTicker(symbol) {
        this.subscribe('price_updates', symbol);
        this.subscribe('prediction_updates', symbol);
    }

    unsubscribeFromTicker(symbol) {
        this.unsubscribe('price_updates', symbol);
        this.unsubscribe('prediction_updates', symbol);
    }

    subscribeToPortfolio() {
        this.subscribe('portfolio_updates');
    }

    subscribeToMarketAlerts() {
        this.subscribe('market_alerts');
    }

    // Message sending
    send(type, payload = {}) {
        const message = {
            type: type,
            payload: payload,
            timestamp: Date.now()
        };
        
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
            console.log('WebSocketClient: Message sent', type);
        } else {
            console.log('WebSocketClient: Queued message', type);
            this.messageQueue.push(message);
        }
    }

    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            if (this.socket.readyState === WebSocket.OPEN) {
                this.socket.send(JSON.stringify(message));
                console.log('WebSocketClient: Sent queued message', message.type);
            } else {
                // Put it back if connection failed
                this.messageQueue.unshift(message);
                break;
            }
        }
    }

    restoreSubscriptions() {
        this.subscriptions.forEach(subscriptionStr => {
            try {
                const subscription = JSON.parse(subscriptionStr);
                this.send('subscribe', subscription);
            } catch (error) {
                console.error('WebSocketClient: Failed to restore subscription', error);
            }
        });
    }

    // Connection management
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
            
            console.log(`WebSocketClient: Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, delay);
        } else {
            console.error('WebSocketClient: Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            
            if (window.app) {
                window.app.showErrorMessage(
                    'Connection Lost', 
                    'Unable to maintain real-time connection. Please refresh the page.'
                );
            }
        }
    }

    handleConnectionError(error) {
        this.updateConnectionStatus('error');
        
        if (this.reconnectAttempts === 0) {
            // First error, show user-friendly message
            if (window.app) {
                window.app.showWarningMessage('Real-time features may be limited due to connection issues');
            }
        }
    }

    // Heartbeat mechanism
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send('heartbeat', { timestamp: Date.now() });
            }
        }, 30000); // 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    // Event listener management
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`WebSocketClient: Event listener error for ${event}`, error);
                }
            });
        }
    }

    // UI update methods
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('ws-status');
        if (statusElement) {
            statusElement.className = `ws-status ${status}`;
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
        
        // Update navigation bar indicator
        const navIndicator = document.querySelector('.realtime-indicator');
        if (navIndicator) {
            navIndicator.className = `realtime-indicator ${status}`;
        }
    }

    updatePriceDisplays(symbol, price, change) {
        // Update all price displays for this symbol
        const priceElements = document.querySelectorAll(`[data-symbol="${symbol}"] .price, [data-ticker="${symbol}"] .current-price`);
        
        priceElements.forEach(element => {
            element.textContent = `$${price.toFixed(2)}`;
            
            // Add price change animation
            element.classList.add('price-updated');
            setTimeout(() => {
                element.classList.remove('price-updated');
            }, 1000);
        });
        
        // Update change displays
        const changeElements = document.querySelectorAll(`[data-symbol="${symbol}"] .change, [data-ticker="${symbol}"] .price-change`);
        
        changeElements.forEach(element => {
            const changeClass = change >= 0 ? 'text-success' : 'text-danger';
            element.className = `change ${changeClass}`;
            element.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
        });
    }

    updatePredictionDisplays(symbol, prediction, confidence, model) {
        const predictionElements = document.querySelectorAll(`[data-symbol="${symbol}"] .prediction`);
        
        predictionElements.forEach(element => {
            element.textContent = `$${prediction.toFixed(2)}`;
            
            // Update confidence if displayed
            const confidenceElement = element.parentNode.querySelector('.confidence');
            if (confidenceElement) {
                confidenceElement.textContent = `${(confidence * 100).toFixed(1)}%`;
            }
        });
    }

    updateCharts(symbol, price, timestamp) {
        // Update Chart.js charts if they exist
        if (window.Chart && window.Chart.instances) {
            window.Chart.instances.forEach(chart => {
                if (chart.canvas.dataset.symbol === symbol) {
                    // Add new data point
                    chart.data.labels.push(new Date(timestamp).toLocaleTimeString());
                    chart.data.datasets[0].data.push(price);
                    
                    // Keep only last 50 points
                    if (chart.data.labels.length > 50) {
                        chart.data.labels.shift();
                        chart.data.datasets[0].data.shift();
                    }
                    
                    chart.update('none'); // No animation for real-time updates
                }
            });
        }
    }

    checkPriceAlerts(symbol, price) {
        // Check if price triggers any alerts
        const alerts = JSON.parse(localStorage.getItem('price-alerts') || '[]');
        
        alerts.forEach(alert => {
            if (alert.symbol === symbol && alert.active) {
                let triggered = false;
                
                if (alert.type === 'above' && price >= alert.threshold) {
                    triggered = true;
                } else if (alert.type === 'below' && price <= alert.threshold) {
                    triggered = true;
                }
                
                if (triggered) {
                    this.triggerAlert(alert, price);
                }
            }
        });
    }

    triggerAlert(alert, currentPrice) {
        // Show notification
        this.showAlertNotification('high', 
            `${alert.symbol} price alert: $${currentPrice.toFixed(2)}`, 
            alert.symbol
        );
        
        // Send push notification if supported
        this.sendPushNotification(
            `${alert.symbol} Price Alert`,
            `Price has reached $${currentPrice.toFixed(2)}`
        );
        
        // Mark alert as triggered
        alert.triggered = true;
        alert.triggeredAt = new Date().toISOString();
        
        // Update stored alerts
        const alerts = JSON.parse(localStorage.getItem('price-alerts') || '[]');
        const index = alerts.findIndex(a => a.id === alert.id);
        if (index > -1) {
            alerts[index] = alert;
            localStorage.setItem('price-alerts', JSON.stringify(alerts));
        }
    }

    showAlertNotification(level, message, symbol) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert-notification level-${level}`;
        notification.innerHTML = `
            <div class="alert-icon">
                <i data-feather="${level === 'high' ? 'alert-circle' : 'info'}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-message">${message}</div>
                <div class="alert-symbol">${symbol}</div>
            </div>
            <button class="alert-close" onclick="this.parentNode.remove()">
                <i data-feather="x"></i>
            </button>
        `;
        
        // Add to notification container
        let container = document.getElementById('alert-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'alert-notifications';
            container.className = 'alert-notifications-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 10000);
        
        // Replace feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    sendPushNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: body,
                icon: '/static/manifest.json',
                badge: '/static/manifest.json',
                tag: 'fullstock-alert'
            });
        }
    }

    // Public API methods
    isConnectionActive() {
        return this.isConnected && this.socket.readyState === WebSocket.OPEN;
    }

    getConnectionStats() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            subscriptions: this.subscriptions.size,
            queuedMessages: this.messageQueue.length
        };
    }

    disconnect() {
        console.log('WebSocketClient: Disconnecting...');
        this.stopHeartbeat();
        
        if (this.socket) {
            this.socket.close(1000, 'Client disconnect');
        }
        
        this.isConnected = false;
        this.subscriptions.clear();
        this.messageQueue = [];
        this.eventListeners.clear();
    }

    reconnect() {
        console.log('WebSocketClient: Manual reconnect requested');
        this.disconnect();
        setTimeout(() => {
            this.reconnectAttempts = 0;
            this.connect();
        }, 1000);
    }
}

// Auto-initialize WebSocket client
if (typeof window !== 'undefined') {
    window.WebSocketClient = WebSocketClient;
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        if (!window.wsClient) {
            window.wsClient = new WebSocketClient();
        }
    });
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}
