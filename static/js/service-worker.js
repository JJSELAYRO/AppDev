// Service Worker for QR Attendance System PWA
// Handles offline caching and background sync

const CACHE_NAME = 'qr-attendance-v1';
const STATIC_ASSETS = [
    '/',
    '/static/css/custom.css',
    '/static/js/offline-sync.js',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    '/accounts/login/',
    '/pwa/offline/'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[Service Worker] Skip waiting');
                return self.skipWaiting();
            })
            .catch((err) => {
                console.error('[Service Worker] Cache failed:', err);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME)
                        .map((name) => {
                            console.log('[Service Worker] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[Service Worker] Claiming clients');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip chrome-extension and other non-http(s) requests
    if (!url.protocol.startsWith('http')) {
        return;
    }
    
    // API requests - network first, no cache
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/qr/')) {
        event.respondWith(
            fetch(request)
                .catch(() => {
                    // If offline, return offline page for HTML requests
                    if (request.headers.get('accept').includes('text/html')) {
                        return caches.match('/pwa/offline/');
                    }
                    return new Response('Offline', { status: 503 });
                })
        );
        return;
    }
    
    // Static assets - cache first
    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // Return cached response and update cache in background
                    fetch(request)
                        .then((networkResponse) => {
                            if (networkResponse.ok) {
                                caches.open(CACHE_NAME)
                                    .then((cache) => cache.put(request, networkResponse));
                            }
                        })
                        .catch(() => {}); // Ignore network errors
                    
                    return cachedResponse;
                }
                
                // Not in cache - fetch from network
                return fetch(request)
                    .then((networkResponse) => {
                        if (!networkResponse || networkResponse.status !== 200) {
                            return networkResponse;
                        }
                        
                        // Clone response and cache it
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => cache.put(request, responseToCache));
                        
                        return networkResponse;
                    })
                    .catch(() => {
                        // Network failed - serve offline page
                        if (request.headers.get('accept').includes('text/html')) {
                            return caches.match('/pwa/offline/');
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Background sync for offline attendance
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-attendance') {
        console.log('[Service Worker] Background sync triggered');
        event.waitUntil(syncAttendanceData());
    }
});

// Function to sync attendance data
async function syncAttendanceData() {
    try {
        const clients = await self.clients.matchAll();
        
        // Notify all clients to sync their data
        clients.forEach((client) => {
            client.postMessage({
                type: 'SYNC_ATTENDANCE',
                message: 'Sync attendance data now'
            });
        });
        
        return Promise.resolve();
    } catch (error) {
        console.error('[Service Worker] Sync failed:', error);
        return Promise.reject(error);
    }
}

// Push notification handling (for future enhancement)
self.addEventListener('push', (event) => {
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body || 'QR Attendance Notification',
            icon: '/static/images/icon-192x192.png',
            badge: '/static/images/icon-72x72.png',
            tag: data.tag || 'default',
            requireInteraction: true,
            actions: [
                {
                    action: 'open',
                    title: 'Open App'
                },
                {
                    action: 'close',
                    title: 'Close'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(
                data.title || 'QR Attendance',
                options
            )
        );
    }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open' || !event.action) {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
});
