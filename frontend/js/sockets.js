/**
 * Lightweight WebSocket client for FullStock AI
 * Handles connection, logging and reconnection with backoff
 */

let ws = null;
let reconnectAttempts = 0;
let warningTimer = null;
const MAX_BACKOFF = 30000; // 30s

function initializeWebSocket() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}/ws/quotes`;
    connect(url);
}

function connect(url) {
    ws = new WebSocket(url);
    console.log('Attempting WebSocket connection to', url);

    // Warn user if connection not established in 5s
    warningTimer = setTimeout(() => {
        showWsWarning();
        if (typeof forceReset === 'function') {
            forceReset();
        }
    }, 5000);

    ws.onopen = () => {
        console.log('WebSocket opened', { readyState: ws.readyState });
        reconnectAttempts = 0;
        clearTimeout(warningTimer);
        hideWsWarning();
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received', data);
            if (data.ticker && typeof updateLiveUpdates === 'function') {
                updateLiveUpdates(`📈 ${data.ticker} update`);
            }
            hideWsWarning();
        } catch (err) {
            console.error('Error parsing WebSocket message', err);
        }
    };

    ws.onerror = (event) => {
        console.error('WebSocket error', { readyState: ws.readyState, event });
    };

    ws.onclose = (event) => {
        console.warn('WebSocket closed', {
            readyState: ws.readyState,
            code: event.code,
            reason: event.reason
        });
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

