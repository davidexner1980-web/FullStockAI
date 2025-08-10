/**
 * Lightweight WebSocket client for FullStock AI
 * Handles connection, logging and reconnection with backoff
 */

let ws = null;
let reconnectAttempts = 0;
let warningTimer = null;
const MAX_BACKOFF = 30000; // 30s

// Build WS URL from current page origin
const proto = location.protocol === 'https:' ? 'wss' : 'ws';
const WS_URL = `${proto}://${location.host}/ws/quotes`;

function initializeWebSocket() {
    connect(WS_URL);
}

function connect(url) {
    ws = new WebSocket(url);
    console.log(`Attempting WebSocket connection to ${url} (attempt ${reconnectAttempts + 1})`);

    // Warn user if connection not established in 5s
    warningTimer = setTimeout(() => {
        showWsWarning();
    }, 5000);

    ws.onopen = () => {
        console.log('WebSocket opened', { url, readyState: ws.readyState });
        reconnectAttempts = 0;
        clearTimeout(warningTimer);
        hideWsWarning();
        if (typeof hideLoadingState === 'function') {
            hideLoadingState();
        }
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received', data);
            if (data.ticker && typeof window.updateLiveUpdates === 'function') {
                window.updateLiveUpdates(`📈 ${data.ticker} update`);
            }
            hideWsWarning();
        } catch (err) {
            console.error('Error parsing WebSocket message', err);
        }
    };

    ws.onerror = (event) => {
        console.error('WebSocket error', { url, readyState: ws.readyState, event });
    };

    ws.onclose = (event) => {
        console.warn('WebSocket closed', {
            url,
            readyState: ws.readyState,
            code: event.code,
            reason: event.reason
        });
        clearTimeout(warningTimer);
        scheduleReconnect(url);
    };
}

function scheduleReconnect(url) {
    reconnectAttempts += 1;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), MAX_BACKOFF);
    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})`);
    setTimeout(() => connect(url), delay);
    if (typeof forceReset === 'function') {
        forceReset();
    }
}

function showWsWarning() {
    const banner = document.getElementById('wsWarning');
    if (banner) {
        banner.style.display = 'block';
    }
    if (typeof hideLoadingState === 'function') {
        hideLoadingState();
    }
}

function hideWsWarning() {
    const banner = document.getElementById('wsWarning');
    if (banner) {
        banner.style.display = 'none';
    }
}

function cleanupWebSocket() {
    if (ws) {
        ws.close();
        ws = null;
    }
    if (warningTimer) {
        clearTimeout(warningTimer);
        warningTimer = null;
    }
}

// Export functions globally
window.initializeWebSocket = initializeWebSocket;
window.cleanupWebSocket = cleanupWebSocket;

// Ensure cleanup on page unload
window.addEventListener('beforeunload', cleanupWebSocket);

