/* ProjectApp panel: network-only navigation with a self-contained offline page.
 * No Cache Storage, API caching, background writes or forced updates.
 * Keep this at /sw.js: /static/frontend/ has immutable caching in nginx.
 */
const offlineMessages = {
  es: {
    title: 'Sin conexión',
    description: 'Necesitas conexión a internet para abrir el panel de ProjectApp. Comprueba tu conexión e inténtalo de nuevo.',
    retry: 'Reintentar',
  },
  en: {
    title: 'You are offline',
    description: 'You need an internet connection to open the ProjectApp panel. Check your connection and try again.',
    retry: 'Retry',
  },
};

function offlineResponse(url) {
  // The login redirect carries the original panel path in next.
  const destination = url.pathname === '/admin/login/' ? url.searchParams.get('next') || '' : url.pathname;
  const language = destination.startsWith('/en-us/') ? 'en' : 'es';
  const message = offlineMessages[language];
  // No request values are interpolated into HTML. Reload retains the original URL.
  return new Response(`<!doctype html>
<html lang="${language}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#002921"><title>${message.title} | ProjectApp</title>
<style>
  *{box-sizing:border-box}body{margin:0;min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:24px;background:#f5f7f6;color:#002921;font:18px/1.6 system-ui,sans-serif}
  main{max-width:460px}h1{line-height:1.2}button{padding:12px 24px;min-height:44px;border:0;border-radius:12px;background:#002921;color:white;font:inherit;cursor:pointer}
  button:focus-visible{outline:3px solid #297a63;outline-offset:4px}
</style></head>
<body><main><p>ProjectApp</p><h1>${message.title}</h1><p>${message.description}</p>
<button type="button" onclick="location.reload()">${message.retry}</button></main></body></html>`, {
    status: 503,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}

self.addEventListener('activate', (event) => {
  // Claim on the first install. Later versions wait for existing clients to close.
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET' || request.mode !== 'navigate') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  const isPanel = /^\/(?:(?:es-co|en-us)\/)?panel(?:\/|$)/.test(url.pathname);
  const isLogin = url.pathname === '/admin/login/';
  if (!isPanel && !isLogin) return;
  // HTTP errors keep their original response. Only a network failure falls back.
  event.respondWith(fetch(request).catch(() => offlineResponse(url)));
});
