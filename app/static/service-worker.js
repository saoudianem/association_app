// ✅ Nom du cache (tu peux changer la version si tu modifies ce fichier)
const CACHE_NAME = "association-chat-v1";

// ✅ Liste des fichiers essentiels à mettre en cache
const URLS_TO_CACHE = [
  "/",
  "/static/style.css",
  "/static/manifest.json"
];

// ✅ Installation : mise en cache initiale
self.addEventListener("install", event => {
  console.log("📦 Service Worker installé");
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(URLS_TO_CACHE))
  );
});

// ✅ Activation : nettoyage des anciens caches
self.addEventListener("activate", event => {
  console.log("🚀 Service Worker activé");
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(key => caches.delete(key))
      );
    })
  );
});

// ✅ Interception des requêtes : on sert depuis le cache si possible
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
      .catch(() => caches.match("/"))
  );
});
