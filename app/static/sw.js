// DARKNOVA AI service worker: caches the app shell only. API/user data is NEVER cached.
const VERSION = 'darknova-v1';
const SHELL = ['/', '/manifest.webmanifest', '/static/logo.jpg', '/static/icons/icon-192.png', '/static/icons/icon-512.png'];
const BYPASS = ['/auth', '/users', '/conversations', '/chat', '/system', '/health', '/media', '/docs', '/redoc', '/openapi.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => Promise.all(SHELL.map((u) => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSION).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});

function bypass(path) {
  return BYPASS.some((p) => path === p || path.startsWith(p + '/'));
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || bypass(url.pathname)) return;

  if (req.mode === 'navigate') {  // network first, offline fallback to cached shell
    e.respondWith(fetch(req).then((res) => {
      if (res.ok && url.pathname === '/') { const copy = res.clone(); caches.open(VERSION).then((c) => c.put('/', copy)); }
      return res;
    }).catch(() => caches.match('/').then((r) => r || new Response('ออฟไลน์ และยังไม่มีข้อมูลที่แคชไว้', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }))));
    return;
  }
  if (url.pathname.startsWith('/static/') || url.pathname === '/manifest.webmanifest') {  // stale-while-revalidate
    e.respondWith(caches.open(VERSION).then((c) => c.match(req).then((hit) => {
      const net = fetch(req).then((res) => { if (res.ok) c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })));
  }
});
