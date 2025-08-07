const CACHE_NAME = 'fullstock-ai-v1.2.0';
const STATIC_CACHE_NAME = 'fullstock-static-v1.2.0';
const API_CACHE_NAME = 'fullstock-api-v1.2.0';

// Files to cache for offline functionality
const STATIC_FILES = [
    '/',
    '/static/css/main.css',
    '/static/css/mobile.css',
    '/static/js/app.js',
    '/static/js/crypto-tracker.js',
    '/static/js/portfolio-manager.js',
    '/static/js/mobile-gestures.js',
    '/static/js/websocket-client.js',
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/chart.js@4.0.0/dist/chart.min.js',
    'https://cdn.jsdelivr.net/npm/feather-icons@4.29.0/dist/feather.min.js'
];

// API endpoints to cache with TTL
const API_CACHE_PATTERNS = [
    /\/api\/predict\/.+/,
    /\/api\/crypto\/predict\/.+/,
    /\/api\/chart_data\/.+/,
    /\/api\/sentiment\/.+/,
    /\/api\/crypto\/market_overview/,
    /\/api\/crypto\/top_gainers/
];

// Cache duration in milliseconds
const CACHE_DURATION = {
    static: 7 * 24 * 60 * 60 * 1000, // 7 days
    api: 5 * 60 * 1000, // 5 minutes
    predictions: 10 * 60 * 1000 // 10 minutes
};

// Install event - cache static files
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE_NAME).then(cache => {
                console.log('Service Worker: Caching static files');
                return cache.addAll(STATIC_FILES);
            }),
            caches.open(API_CACHE_NAME).then(cache => {
                console.log('Service Worker: API cache initialized');
                return Promise.resolve();
            })
        ]).then(() => {
            console.log('Service Worker: Installation complete');
            return self.skipWaiting();
        }).catch(error => {
            console.error('Service Worker: Installation failed', error);
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== API_CACHE_NAME && 
                        cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('Service Worker: Activation complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
    } else if (url.pathname.startsWith('/static/') || STATIC_FILES.includes(url.pathname)) {
        event.respondWith(handleStaticRequest(request));
    } else {
        event.respondWith(handleNavigationRequest(request));
    }
});

// Handle API requests with caching strategy
async function handleApiRequest(request) {
    const url = new URL(request.url);
    const cacheName = API_CACHE_NAME;
    
    try {
        // Check if this API should be cached
        const shouldCache = API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
        
        if (!shouldCache) {
            // For real-time data, always fetch from network
            return await fetch(request);
        }
        
        const cache = await caches.open(cacheName);
        const cachedResponse = await cache.match(request);
        
        // Check if cached response is still valid
        if (cachedResponse) {
            const cachedTime = new Date(cachedResponse.headers.get('sw-cached-time'));
            const now = new Date();
            const maxAge = url.pathname.includes('predict') ? CACHE_DURATION.predictions : CACHE_DURATION.api;
            
            if (now - cachedTime < maxAge) {
                console.log('Service Worker: Serving from API cache', url.pathname);
                return cachedResponse;
            }
        }
        
        // Fetch from network and cache the response
        try {
            const networkResponse = await fetch(request);
            
            if (networkResponse.ok) {
                const responseToCache = networkResponse.clone();
                
                // Add timestamp header
                const headers = new Headers(responseToCache.headers);
                headers.set('sw-cached-time', new Date().toISOString());
                
                const modifiedResponse = new Response(responseToCache.body, {
                    status: responseToCache.status,
                    statusText: responseToCache.statusText,
                    headers: headers
                });
                
                cache.put(request, modifiedResponse);
                console.log('Service Worker: Cached API response', url.pathname);
            }
            
            return networkResponse;
        } catch (error) {
            console.log('Service Worker: Network failed, serving stale cache', url.pathname);
            return cachedResponse || new Response(
                JSON.stringify({ error: 'Network unavailable', cached: false }),
                { status: 503, headers: { 'Content-Type': 'application/json' } }
            );
        }
    } catch (error) {
        console.error('Service Worker: API request failed', error);
        return new Response(
            JSON.stringify({ error: 'Service unavailable' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
    }
}

// Handle static file requests
async function handleStaticRequest(request) {
    try {
        const cache = await caches.open(STATIC_CACHE_NAME);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            console.log('Service Worker: Serving from static cache', request.url);
            return cachedResponse;
        }
        
        // Fetch from network and cache
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
            console.log('Service Worker: Cached static file', request.url);
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Service Worker: Static request failed', error);
        return new Response('File not available offline', { status: 404 });
    }
}

// Handle navigation requests (HTML pages)
async function handleNavigationRequest(request) {
    try {
        // Try network first for navigation
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        // Fallback to cached index page for offline functionality
        const cache = await caches.open(STATIC_CACHE_NAME);
        const fallbackResponse = await cache.match('/');
        
        if (fallbackResponse) {
            console.log('Service Worker: Serving offline fallback');
            return fallbackResponse;
        }
        
        return new Response('App not available offline', {
            status: 503,
            headers: { 'Content-Type': 'text/plain' }
        });
    }
}

// Background sync for queued requests
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    if (event.tag === 'prediction-requests') {
        event.waitUntil(processPendingPredictions());
    } else if (event.tag === 'portfolio-updates') {
        event.waitUntil(processPendingPortfolioUpdates());
    }
});

// Process pending prediction requests
async function processPendingPredictions() {
    try {
        const requests = await getStoredRequests('predictions');
        
        for (const requestData of requests) {
            try {
                const response = await fetch(requestData.url, requestData.options);
                
                if (response.ok) {
                    // Notify clients of successful sync
                    self.clients.matchAll().then(clients => {
                        clients.forEach(client => {
                            client.postMessage({
                                type: 'PREDICTION_SYNCED',
                                data: { url: requestData.url, success: true }
                            });
                        });
                    });
                    
                    // Remove from pending requests
                    await removeStoredRequest('predictions', requestData.id);
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync prediction request', error);
            }
        }
    } catch (error) {
        console.error('Service Worker: Background sync failed', error);
    }
}

// Process pending portfolio updates
async function processPendingPortfolioUpdates() {
    try {
        const requests = await getStoredRequests('portfolio');
        
        for (const requestData of requests) {
            try {
                const response = await fetch(requestData.url, requestData.options);
                
                if (response.ok) {
                    // Notify clients of successful sync
                    self.clients.matchAll().then(clients => {
                        clients.forEach(client => {
                            client.postMessage({
                                type: 'PORTFOLIO_SYNCED',
                                data: { url: requestData.url, success: true }
                            });
                        });
                    });
                    
                    // Remove from pending requests
                    await removeStoredRequest('portfolio', requestData.id);
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync portfolio request', error);
            }
        }
    } catch (error) {
        console.error('Service Worker: Portfolio sync failed', error);
    }
}

// Utility functions for IndexedDB operations
async function getStoredRequests(storeName) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FullStockAI', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => resolve(getAllRequest.result);
            getAllRequest.onerror = () => reject(getAllRequest.error);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('predictions')) {
                db.createObjectStore('predictions', { keyPath: 'id', autoIncrement: true });
            }
            
            if (!db.objectStoreNames.contains('portfolio')) {
                db.createObjectStore('portfolio', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

async function removeStoredRequest(storeName, id) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('FullStockAI', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const deleteRequest = store.delete(id);
            
            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('Service Worker: Push notification received');
    
    const options = {
        body: 'Check your portfolio for updates',
        icon: '/static/manifest.json',
        badge: '/static/manifest.json',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'view',
                title: 'View Portfolio',
                icon: '/static/manifest.json'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/manifest.json'
            }
        ]
    };
    
    if (event.data) {
        const data = event.data.json();
        options.body = data.message || options.body;
        options.data = { ...options.data, ...data };
    }
    
    event.waitUntil(
        self.registration.showNotification('FullStock AI Alert', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('Service Worker: Notification clicked');
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/portfolio')
        );
    } else if (event.action === 'close') {
        // Just close the notification
        return;
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.matchAll().then(clientList => {
                for (const client of clientList) {
                    if (client.url === '/' && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                if (clients.openWindow) {
                    return clients.openWindow('/');
                }
            })
        );
    }
});

// Message handling from main thread
self.addEventListener('message', event => {
    console.log('Service Worker: Message received', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data && event.data.type === 'CACHE_PREDICTION') {
        // Cache prediction request for background sync
        cacheRequestForSync('predictions', event.data.request);
    } else if (event.data && event.data.type === 'CACHE_PORTFOLIO') {
        // Cache portfolio update for background sync
        cacheRequestForSync('portfolio', event.data.request);
    }
});

// Cache request for background sync
async function cacheRequestForSync(storeName, requestData) {
    try {
        const request = indexedDB.open('FullStockAI', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            store.add({
                url: requestData.url,
                options: requestData.options,
                timestamp: Date.now()
            });
        };
    } catch (error) {
        console.error('Service Worker: Failed to cache request for sync', error);
    }
}

console.log('Service Worker: Script loaded');
