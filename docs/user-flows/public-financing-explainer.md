### FLOW: `public-financing-explainer`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Ruta:** `/:locale/financing`
- **Interacción:** Reproducir el video explicativo desde el hero (debajo del
  subtítulo y antes de los botones de WhatsApp y PDF) con sonido y controles
  nativos; si el navegador no puede reproducirlo, abrir el archivo desde el
  enlace de respaldo. En inglés la tarjeta no aparece hasta tener el render en
  ese idioma.
- **Outcomes:** `display`, `success`, `failure`
- **Evidencia:** `ExplainerVideoCard.vue`, `useExplainerVideos.js`,
  `Financing/ProgramView.vue` y `e2e/public/financing.spec.js`.
