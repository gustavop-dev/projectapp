### FLOW: `public-additional-modules-explainer`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Rutas:** `/:locale/additional-modules` y
  `/:locale/additional-modules/share/:uuid`
- **Interacción:** Encontrar la tarjeta del video explicativo debajo del título
  (primer bloque antes del primer módulo), reproducirlo en el mismo lugar con
  sonido y controles nativos, y usar el enlace directo al archivo si el
  navegador no puede reproducirlo. En inglés la tarjeta no aparece hasta tener
  el render en ese idioma.
- **Outcomes:** `display`, `success`, `failure`
- **Evidencia:** `ExplainerVideoCard.vue`, `useExplainerVideos.js`,
  `AdditionalModules/CatalogView.vue` y `e2e/public/additional-modules.spec.js`.
