// FullStock AI vNext Ultimate Service Worker
// Progressive Web App functionality

const CACHE_NAME = 'fullstock-ai-v2.0.0';
const CACHE_VERSION = '2.0.0';

// Assets to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/static/css/main.css',
  '/static/css/mobile.css',
  '/static/js/app.js',
  '/static/js/mobile.js',
  '/static/js/notifications.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/chart.js@4.0.0/dist/chart.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// API endpoints to cache with network-first strategy
const API_ENDPOINTS = [
  '/api/predict/',
  '/api/crypto/predict/',
  '/api/oracle/',
  '/api/strategies/',
  '/api/chart_data/',
  '/api/health_status'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker installed successfully');
        return self.skipWaiting(); // Activate immediately
      })
      .catch(error => {
        console.error('Service Worker installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => cacheName !== CACHE_NAME)
            .map(cacheName => {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('Service Worker activated successfully');
        return self.clients.claim(); // Take control immediately
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different types of requests
  if (isAPIRequest(url)) {
    // API requests: Network-first with cache fallback
    event.respondWith(networkFirstStrategy(request));
  } else if (isStaticAsset(url)) {
    // Static assets: Cache-first with network fallback
    event.respondWith(cacheFirstStrategy(request));
  } else {
    // HTML pages: Network-first with cache fallback
    event.respondWith(networkFirstStrategy(request));
  }
});

// Network-first strategy for dynamic content
async function networkFirstStrategy(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Network failed, trying cache:', request.url);
    
    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for HTML requests
    if (request.headers.get('Accept')?.includes('text/html')) {
      return createOfflineResponse();
    }
    
    // Return empty response for other requests
    return new Response('Offline', { 
      status: 503, 
      statusText: 'Service Unavailable' 
    });
  }
}

// Cache-first strategy for static assets
async function cacheFirstStrategy(request) {
  try {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback to network
    const networkResponse = await fetch(request);
    
    // Cache the response
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache and network both failed:', error);
    return new Response('Asset not available offline', { 
      status: 503, 
      statusText: 'Service Unavailable' 
    });
  }
}

// Check if request is for API endpoint
function isAPIRequest(url) {
  return url.pathname.startsWith('/api/') || 
         API_ENDPOINTS.some(endpoint => url.pathname.startsWith(endpoint));
}

// Check if request is for static asset
function isStaticAsset(url) {
  return url.pathname.startsWith('/static/') ||
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.svg') ||
         url.pathname.endsWith('.ico') ||
         url.hostname !== self.location.hostname; // External CDN assets
}

// Create offline response for HTML pages
function createOfflineResponse() {
  const offlineHTML = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>FullStock AI - Offline</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: linear-gradient(135deg, #0d1117 0%, #1f2937 100%);
          color: #ffffff;
          margin: 0;
          padding: 0;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .offline-container {
          text-align: center;
          padding: 2rem;
          max-width: 500px;
        }
        .offline-icon {
          font-size: 4rem;
          color: #fbbf24;
          margin-bottom: 1rem;
        }
        .offline-title {
          font-size: 2rem;
          font-weight: bold;
          margin-bottom: 1rem;
          color: #ffffff;
        }
        .offline-message {
          font-size: 1.1rem;
          color: #d1d5db;
          margin-bottom: 2rem;
          line-height: 1.6;
        }
        .retry-button {
          background: linear-gradient(45deg, #3b82f6, #1d4ed8);
          color: white;
          border: none;
          padding: 0.75rem 2rem;
          border-radius: 0.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }
        .retry-button:hover {
          transform: translateY(-2px);
        }
        .oracle-wisdom {
          margin-top: 2rem;
          padding: 1rem;
          background: rgba(59, 130, 246, 0.1);
          border-radius: 0.5rem;
          border-left: 4px solid #3b82f6;
          font-style: italic;
          color: #93c5fd;
        }
      </style>
    </head>
    <body>
      <div class="offline-container">
        <div class="offline-icon">🔮</div>
        <h1 class="offline-title">Oracle Mode: Offline</h1>
        <p class="offline-message">
          The cosmic connection has been temporarily disrupted. 
          Your device holds cached wisdom from previous sessions.
        </p>
        <button class="retry-button" onclick="window.location.reload()">
          Reconnect to the Oracle
        </button>
        <div class="oracle-wisdom">
          "In disconnection, we find the wisdom stored within. 
          The Oracle's insights remain accessible through the quantum cache."
        </div>
      </div>
    </body>
    </html>
  `;
  
  return new Response(offlineHTML, {
    headers: {
      'Content-Type': 'text/html',
      'Cache-Control': 'no-cache'
    }
  });
}

// Handle background sync for data updates
self.addEventListener('sync', event => {
  console.log('Background sync triggered:', event.tag);
  
  if (event.tag === 'price-update') {
    event.waitUntil(syncPriceData());
  } else if (event.tag === 'prediction-update') {
    event.waitUntil(syncPredictionData());
  }
});

// Sync price data in background
async function syncPriceData() {
  try {
    // Get cached watchlist
    const cache = await caches.open(CACHE_NAME);
    const watchlistResponse = await cache.match('/api/watchlist');
    
    if (watchlistResponse) {
      const watchlist = await watchlistResponse.json();
      
      // Update prices for watchlist items
      for (const ticker of watchlist) {
        try {
          const response = await fetch(`/api/predict/${ticker}`);
          if (response.ok) {
            cache.put(`/api/predict/${ticker}`, response.clone());
          }
        } catch (error) {
          console.log(`Failed to sync ${ticker}:`, error);
        }
      }
    }
    
    console.log('Price data sync completed');
  } catch (error) {
    console.error('Price data sync failed:', error);
  }
}

// Sync prediction data in background
async function syncPredictionData() {
  try {
    // Update health status
    const healthResponse = await fetch('/api/health_status');
    if (healthResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put('/api/health_status', healthResponse.clone());
    }
    
    console.log('Prediction data sync completed');
  } catch (error) {
    console.error('Prediction data sync failed:', error);
  }
}

// Handle push notifications
self.addEventListener('push', event => {
  console.log('Push notification received');
  
  let notificationData = {
    title: 'FullStock AI',
    body: 'Market update available',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    tag: 'market-update',
    requireInteraction: false,
    timestamp: Date.now()
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (error) {
      console.error('Failed to parse push data:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event.notification.tag);
  
  event.notification.close();
  
  // Determine URL based on notification tag
  let targetUrl = '/';
  switch (event.notification.tag) {
    case 'price-alert':
      targetUrl = '/?alert=price';
      break;
    case 'prediction-update':
      targetUrl = '/?update=prediction';
      break;
    case 'oracle-insight':
      targetUrl = '/?oracle=true';
      break;
    case 'crypto-update':
      targetUrl = '/crypto';
      break;
    case 'portfolio-update':
      targetUrl = '/portfolio';
      break;
  }
  
  // Open or focus the app
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clientList => {
        // Try to focus existing window
        for (const client of clientList) {
          if (client.url.startsWith(self.location.origin)) {
            client.navigate(targetUrl);
            return client.focus();
          }
        }
        
        // Open new window if none exists
        return clients.openWindow(targetUrl);
      })
  );
});

// Handle message events from the main thread
self.addEventListener('message', event => {
  console.log('Service Worker received message:', event.data);
  
  const { type, payload } = event.data;
  
  switch (type) {
    case 'CACHE_TICKER':
      cacheTicker(payload.ticker);
      break;
    case 'CLEAR_CACHE':
      clearCache();
      break;
    case 'UPDATE_CACHE':
      updateCache();
      break;
    case 'GET_CACHE_STATUS':
      getCacheStatus().then(status => {
        event.ports[0]?.postMessage(status);
      });
      break;
  }
});

// Cache specific ticker data
async function cacheTicker(ticker) {
  try {
    const cache = await caches.open(CACHE_NAME);
    const endpoints = [
      `/api/predict/${ticker}`,
      `/api/oracle/${ticker}`,
      `/api/strategies/${ticker}`,
      `/api/chart_data/${ticker}`
    ];
    
    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint);
        if (response.ok) {
          await cache.put(endpoint, response);
        }
      } catch (error) {
        console.log(`Failed to cache ${endpoint}:`, error);
      }
    }
    
    console.log(`Cached data for ticker: ${ticker}`);
  } catch (error) {
    console.error('Failed to cache ticker:', error);
  }
}

// Clear all caches
async function clearCache() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(name => caches.delete(name))
    );
    console.log('All caches cleared');
  } catch (error) {
    console.error('Failed to clear cache:', error);
  }
}

// Update cache with fresh data
async function updateCache() {
  try {
    const cache = await caches.open(CACHE_NAME);
    
    // Update static assets
    for (const asset of STATIC_ASSETS) {
      try {
        const response = await fetch(asset);
        if (response.ok) {
          await cache.put(asset, response);
        }
      } catch (error) {
        console.log(`Failed to update ${asset}:`, error);
      }
    }
    
    console.log('Cache updated successfully');
  } catch (error) {
    console.error('Failed to update cache:', error);
  }
}

// Get cache status information
async function getCacheStatus() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    
    const status = {
      cacheName: CACHE_NAME,
      version: CACHE_VERSION,
      totalItems: keys.length,
      staticAssets: keys.filter(req => isStaticAsset(new URL(req.url))).length,
      apiEndpoints: keys.filter(req => isAPIRequest(new URL(req.url))).length,
      lastUpdated: new Date().toISOString()
    };
    
    return status;
  } catch (error) {
    console.error('Failed to get cache status:', error);
    return { error: 'Failed to get cache status' };
  }
}

// Periodic cache cleanup
setInterval(() => {
  console.log('Running periodic cache cleanup...');
  
  caches.open(CACHE_NAME).then(cache => {
    cache.keys().then(keys => {
      const now = Date.now();
      const maxAge = 24 * 60 * 60 * 1000; // 24 hours
      
      keys.forEach(async request => {
        if (isAPIRequest(new URL(request.url))) {
          const response = await cache.match(request);
          const dateHeader = response?.headers.get('date');
          
          if (dateHeader) {
            const cacheDate = new Date(dateHeader).getTime();
            if (now - cacheDate > maxAge) {
              console.log('Removing expired cache entry:', request.url);
              cache.delete(request);
            }
          }
        }
      });
    });
  });
}, 60 * 60 * 1000); // Run every hour

console.log('FullStock AI Service Worker loaded successfully');
