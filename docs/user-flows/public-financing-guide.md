### FLOW: `public-financing-guide`

- **Módulo:** public
- **Rol:** invitado
- **Prioridad:** P2
- **Ruta:** `/:locale/financing`
- **Interacción:** En la primera visita, recorrer la guía del programa (empieza
  en la tarjeta del video explicativo y sigue por opciones, condiciones,
  calculadora, paquete, reglas y acciones flotantes) y cerrarla; en visitas
  posteriores, reiniciarla desde el control flotante. La vista previa del panel
  no la muestra.
- **Outcomes:** `success`, `display`
- **Evidencia:** `PublicGuidedTour.vue`, `Financing/Onboarding.vue`,
  `Financing/ProgramView.vue` y `e2e/public/financing.spec.js`.
