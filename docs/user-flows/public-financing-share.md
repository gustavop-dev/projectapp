### FLOW: `public-financing-share`

- **Module:** public
- **Role:** guest
- **Priority:** P2
- **Route:** `/:locale/partnership-program`
- **Interaction:** Abrir el diálogo de Compartir; copiar la URL exacta (idioma, query y hash) o abrir el selector nativo. Escape devuelve el foco al control flotante.
- **Outcomes:** `success`, `failure`
- **Failure:** Si falla el portapapeles, mostrar un error recuperable dentro del diálogo. Cancelar el selector nativo no es un error.
- **Evidence:** `PublicDocumentShareButton.vue`, montado desde `Financing/ProgramView.vue`.
