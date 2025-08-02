self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('finance-cache').then((cache) => {
      return cache.addAll([
        '/',
        '/static/style.css',
        '/static/icons/icon-192.png',
        '/static/icons/icon-512.png'
      ]);
    })
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
