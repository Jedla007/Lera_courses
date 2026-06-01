/* Service Worker — F1 & WRC 2026
   Stratégie : Network-first, cache en fallback.
   → En ligne  : contenu frais, cache mis à jour en arrière-plan.
   → Hors ligne : sert index.html + data.json depuis le cache.
   Pour forcer une mise à jour : incrémenter CACHE_NAME.            */

const CACHE_NAME = 'f1wrc-2026-v1';
const PRECACHE   = ['/', '/data.json'];

// ── Install : pré-cache l'app shell ──────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// ── Activate : supprime les anciens caches ────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch : network-first, fallback cache ─────────────────────────
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  if (!e.request.url.startsWith(self.location.origin)) return;

  e.respondWith(
    fetch(e.request)
      .then(res => {
        // Met à jour le cache si réponse valide
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
