### FLOW: `admin-additional-modules-share-video`

- **Módulo:** admin
- **Rol:** admin
- **Prioridad:** P2
- **Ruta:** `/:locale/panel/additional-modules` (modales de selección y de
  seguimiento)
- **Interacción:** Al preparar un enlace compartible, apagar "Mostrar el video
  explicativo en este enlace" (útil cuando se comparten pocos módulos y el
  video presenta el catálogo completo). Después, desde el seguimiento, volver
  a encender el video de un enlace puntual. Mientras el interruptor del
  catálogo está apagado, el seguimiento explica que ningún enlace lo muestra:
  el interruptor del catálogo manda sobre el del enlace.
- **Outcomes:** `success`, `display`
- **Evidencia:** `CatalogSelectionModal.vue`, `ShareHistoryModal.vue`,
  `stores/additional_modules.js` (`setShareLinkVideo`),
  `PATCH additional-modules/admin/shares/:uuid/` y
  `e2e/admin/admin-additional-modules.spec.js`.
