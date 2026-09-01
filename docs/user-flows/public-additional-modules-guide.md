### FLOW: `public-additional-modules-guide`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Rutas:** `/:locale/additional-modules` y
  `/:locale/additional-modules/share/:uuid`
- **Interacción:** En la primera visita, recorrer una guía específica del
  catálogo y cerrarla; en visitas posteriores, reiniciarla desde el control
  flotante.
- **Outcomes:** `success`, `display`
- **Evidencia:** `AdditionalModules/Onboarding.vue` y
  `e2e/public/additional-modules.spec.js`.
