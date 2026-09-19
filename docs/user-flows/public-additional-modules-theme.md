### FLOW: `public-additional-modules-theme`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Rutas:** `/:locale/additional-modules` y
  `/:locale/additional-modules/share/:uuid`
- **Interacción:** Alternar entre modo claro y oscuro, leer el índice y el
  detalle con el mismo tema y recuperar esa preferencia en una visita posterior.
- **Outcomes:** `success`, `display`, `failure`
- **Failure:** El mensaje de carga fallida y el catálogo recuperado con
  Reintentar conservan el tema elegido, también en selecciones compartidas.
- **Evidencia:** `useAdditionalModulesTheme.js`, `CatalogView.vue` y
  `e2e/public/additional-modules.spec.js`.
