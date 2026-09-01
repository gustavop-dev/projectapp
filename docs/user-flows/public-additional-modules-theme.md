### FLOW: `public-additional-modules-theme`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Rutas:** `/:locale/additional-modules` y
  `/:locale/additional-modules/share/:uuid`
- **Interacción:** Alternar entre modo claro y oscuro, leer el índice y el
  detalle con el mismo tema y recuperar esa preferencia en una visita posterior.
- **Outcomes:** `success`, `display`
- **Evidencia:** `useAdditionalModulesTheme.js`, `CatalogView.vue` y
  `e2e/public/additional-modules.spec.js`.
