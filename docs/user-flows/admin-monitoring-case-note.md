### FLOW: `admin-monitoring-case-note`

- **Módulo / rol:** monitoreo / administrador del panel.
- **Ruta:** `/panel/monitoring`, modal de caso.
- **Display:** historial con texto, autor y fecha de la nota.
- **Success:** escribir y agregar una nota la incorpora al historial compartido.
- **Error / failure:** un rechazo o fallo de API muestra el error y conserva el texto escrito.
- **API:** `POST /api/monitoring/cases/:id/notes/` y detalle del caso.
- **Cobertura:** `e2e/admin/admin-monitoring-case-follow-up.spec.js`.
