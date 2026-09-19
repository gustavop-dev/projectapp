# admin-pwa-offline — Apertura y recuperación sin conexión

- **Rol:** administrador. **Prioridad:** P2.
- **Entrada:** abrir o recargar la app instalada.
- **Success:** al volver internet, Reintentar recupera la URL original. Abrir
  el start_url sin sesión conduce al login real de Django con next al panel.
- **Failure:** sin conexión, Reintentar mantiene el aviso y la URL.
- **Display:** integrado en el resultado del fallo de navegación.
- **Error:** no agrega validaciones; los HTTP 4xx/5xx conservan su respuesta.
- **Specs:** `frontend/e2e/pwa/panel-offline.spec.js`, ejecutado contra un
  build servido por Django mediante `playwright.pwa.config.js`.
- **Privacidad:** solo falla a una pantalla autónoma; no escribe Cache Storage,
  no guarda respuestas privadas y no encola operaciones. Las exclusiones de
  rutas y métodos se verifican en los tests del worker.
