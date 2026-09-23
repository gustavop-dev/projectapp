### FLOW: `public-additional-modules-theme`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Rutas:** `/:locale/additional-modules` y
  `/:locale/additional-modules/share/:uuid`
- **Interacción:** Alternar entre modo claro y oscuro, leer el índice y el
  detalle con el mismo tema y recuperar esa preferencia en una visita posterior.
- **Presentación:** página, tarjetas e interiores se distinguen en ambos temas;
  las categorías se separan con espacio, sin líneas decorativas. La primera
  entrada de cada sección tiene una transición breve, desactivada con movimiento
  reducido. El nuevo observer no impone un estado oculto previo; su fallback
  ante API no disponible se verifica en pruebas unitarias.
- **Outcomes:** `success`, `display`, `failure`
- **Failure:** El mensaje de carga fallida y el catálogo recuperado con
  Reintentar conservan el tema elegido, también en selecciones compartidas.
- **Evidencia:** `useAdditionalModulesTheme.js`, `CatalogView.vue` y
  `e2e/public/additional-modules.spec.js`, `commercial-public-theme.spec.js`,
  `commercial-public-overlays.spec.js` y `commercial-public-motion.spec.js`.
