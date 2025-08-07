/**
 * FullStock AI Service Worker - PWA Support & Offline Caching
 * Handles caching strategies, offline functionality, and PWA installation
 */

const CACHE_NAME = 'fullstock-ai-v1.0.0';
const STATIC_CACHE_NAME = 'fullstock-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'fullstock-dynamic-v1.0.0';

// Assets to cache for offline functionality
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/crypto.html',
    '/oracle.html', 
    '/portfolio.html',
    '/css/styles.css',
    '/js/dashboard.js',
    '/js/crypto.js',
    '/js/oracle.js',
    '/js/portfolio.js',
    '/js/sockets.js',
    '/js/charts.js',
    '/manifest.json',
    // External CDN resources (cached with different strategy)
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
    'https://unpkg.com/feather-icons',
    'https://cdn.jsdelivr.net/npm/chart.js',
    'https://cdn.socket.io/4.7.2/socket.io.min.js'
];

// API endpoints to cache (with short TTL)
const API_ENDPOINTS = [
    '/api/health',
    '/api/predict/',
    '/api/crypto/predict/',
    '/api/chart_data/',
    '/api/oracle/',
    '/api/portfolio/'
];

// Cache duration settings (in milliseconds)
const CACHE_DURATION = {
    STATIC: 24 * 60 * 60 * 1000,    // 24 hours
    API: 5 * 60 * 1000,             // 5 minutes
    DYNAMIC: 2 * 60 * 60 * 1000     // 2 hours
};

/**
 * Service Worker Installation
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Installing FullStock AI Service Worker');
    
    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE_NAME).then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS.filter(url => !url.includes('https://')));
            }),
            
            // Cache external CDN resources with network-first strategy
            caches.open(STATIC_CACHE_NAME).then(async (cache) => {
                console.log('[SW] Caching external CDN resources');
                const cdnAssets = STATIC_ASSETS.filter(url => url.includes('https://'));
                
                for (const url of cdnAssets) {
                    try {
                        const response = await fetch(url);
                        if (response.ok) {
                            await cache.put(url, response);
                        }
                    } catch (error) {
                        console.warn(`[SW] Failed to cache CDN asset: ${url}`, error);
                    }
                }
            })
        ]).then(() => {
            console.log('[SW] Installation complete');
            // Force activation of new service worker
            return self.skipWaiting();
        })
    );
});

/**
 * Service Worker Activation
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating FullStock AI Service Worker');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old caches
                    if (cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== DYNAMIC_CACHE_NAME &&
                        cacheName !== CACHE_NAME) {
                        console.log(`[SW] Deleting old cache: ${cacheName}`);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Activation complete');
            // Claim all clients immediately
            return self.clients.claim();
        })
    );
});

/**
 * Fetch Event Handler - Main Caching Logic
 */
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Skip non-HTTP requests
    if (!event.request.url.startsWith('http')) {
        return;
    }
    
    // Skip WebSocket requests
    if (url.pathname.includes('socket.io')) {
        return;
    }
    
    event.respondWith(handleRequest(event.request));
});

/**
 * Handle Different Types of Requests
 */
async function handleRequest(request) {
    const url = new URL(request.url);
    
    // API requests - Network first with cache fallback
    if (url.pathname.startsWith('/api/')) {
        return handleAPIRequest(request);
    }
    
    // Static assets - Cache first
    if (isStaticAsset(url.pathname)) {
        return handleStaticAsset(request);
    }
    
    // HTML pages - Network first with cache fallback
    if (request.headers.get('accept')?.includes('text/html')) {
        return handleHTMLRequest(request);
    }
    
    // External CDN resources - Cache first with network fallback
    if (url.origin !== location.origin) {
        return handleExternalResource(request);
    }
    
    // Default: network first
    return handleNetworkFirst(request);
}

/**
 * Handle API Requests - Network First Strategy
 */
async function handleAPIRequest(request) {
    try {
        // Always try network first for real-time data
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful API responses with short TTL
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            const responseClone = networkResponse.clone();
            
            // Add timestamp for TTL checking
            const responseWithTimestamp = new Response(responseClone.body, {
                status: responseClone.status,
                statusText: responseClone.statusText,
                headers: {
                    ...Object.fromEntries(responseClone.headers.entries()),
                    'sw-cached-at': Date.now().toString()
                }
            });
            
            await cache.put(request, responseWithTimestamp);
            return networkResponse;
        }
        
        throw new Error(`API request failed: ${networkResponse.status}`);
        
    } catch (error) {
        console.warn('[SW] API network request failed, trying cache:', error);
        
        // Try cache as fallback
        const cachedResponse = await getCachedResponse(request, DYNAMIC_CACHE_NAME);
        if (cachedResponse && !isCacheExpired(cachedResponse, CACHE_DURATION.API)) {
            console.log('[SW] Serving cached API response');
            return cachedResponse;
        }
        
        // Return offline response for critical API failures
        return createOfflineResponse(request);
    }
}

/**
 * Handle Static Assets - Cache First Strategy  
 */
async function handleStaticAsset(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // If not in cache, fetch and cache
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            await cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.warn('[SW] Static asset fetch failed:', error);
        return new Response('Asset not available offline', { status: 404 });
    }
}

/**
 * Handle HTML Requests - Network First with Cache Fallback
 */
async function handleHTMLRequest(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            // Cache HTML responses
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            await cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        throw new Error(`HTML request failed: ${networkResponse.status}`);
    } catch (error) {
        console.warn('[SW] HTML network request failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page as last resort
        return createOfflinePage();
    }
}

/**
 * Handle External Resources - Cache First with Network Fallback
 */
async function handleExternalResource(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        // Check if cache is expired for CDN resources
        if (!isCacheExpired(cachedResponse, CACHE_DURATION.STATIC)) {
            return cachedResponse;
        }
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            await cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        throw new Error(`External resource failed: ${networkResponse.status}`);
    } catch (error) {
        if (cachedResponse) {
            console.log('[SW] Using expired cache for external resource:', request.url);
            return cachedResponse;
        }
        throw error;
    }
}

/**
 * Handle Network First Strategy
 */
async function handleNetworkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            await cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        throw error;
    }
}

/**
 * Utility Functions
 */
function isStaticAsset(pathname) {
    const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.woff', '.woff2'];
    return staticExtensions.some(ext => pathname.endsWith(ext));
}

async function getCachedResponse(request, cacheName) {
    const cache = await caches.open(cacheName);
    return await cache.match(request);
}

function isCacheExpired(response, maxAge) {
    const cachedAt = response.headers.get('sw-cached-at');
    if (!cachedAt) return false;
    
    const age = Date.now() - parseInt(cachedAt);
    return age > maxAge;
}

function createOfflineResponse(request) {
    const url = new URL(request.url);
    
    if (url.pathname.startsWith('/api/')) {
        return new Response(JSON.stringify({
            error: 'Offline',
            message: 'API unavailable offline',
            offline: true,
            timestamp: new Date().toISOString()
        }), {
            status: 503,
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
    }
    
    return new Response('Service unavailable offline', { 
        status: 503,
        headers: { 'Content-Type': 'text/plain' }
    });
}

function createOfflinePage() {
    const offlineHTML = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FullStock AI - Offline</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
                color: white; 
                text-align: center; 
                padding: 50px; 
                margin: 0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            .offline-icon { font-size: 4rem; margin-bottom: 2rem; }
            h1 { color: #667eea; margin-bottom: 1rem; }
            p { color: #8e9297; font-size: 1.2rem; }
            .retry-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                margin-top: 2rem;
                transition: transform 0.2s;
            }
            .retry-btn:hover { transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="offline-icon">📡</div>
        <h1>You're Offline</h1>
        <p>FullStock AI requires an internet connection for real-time market data.</p>
        <p>Please check your connection and try again.</p>
        <button class="retry-btn" onclick="window.location.reload()">Retry Connection</button>
        
        <script>
            // Auto-retry when back online
            window.addEventListener('online', () => {
                window.location.reload();
            });
        </script>
    </body>
    </html>`;
    
    return new Response(offlineHTML, {
        status: 503,
        headers: { 'Content-Type': 'text/html' }
    });
}

/**
 * Background Sync for Failed Requests
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);
    
    if (event.tag === 'api-retry') {
        event.waitUntil(retryFailedRequests());
    }
});

async function retryFailedRequests() {
    // Implementation for retrying failed API requests when back online
    console.log('[SW] Retrying failed requests...');
}

/**
 * Push Notifications (for future use)
 */
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received:', event);
    
    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.body || 'New market update available',
            icon: '/icons/icon-96x96.png',
            badge: '/icons/badge-72x72.png',
            data: data.data,
            actions: data.actions || []
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'FullStock AI', options)
        );
    }
});

/**
 * Notification Click Handler
 */
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event);
    
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

console.log('[SW] FullStock AI Service Worker loaded successfully');