### FLOW: `admin-monitoring-case-follow-up`

- **Módulo / rol:** monitoreo / administrador del panel.
- **Ruta:** `/panel/monitoring`, modal desde el título de un caso.
- **Display:** evidencia, condición técnica y estado manual separados; historial paginado y enlace al reporte de origen cuando existe.
- **Success:** cambiar Pendiente / En revisión / Resuelto persiste el estado y la autoría.
- **Error:** una versión desactualizada devuelve conflicto y solicita actualizar.
- **Failure:** un fallo de guardado se anuncia sin perder la selección.
- **API:** detalle del caso y `POST /api/monitoring/cases/:id/state/`.
- **Cobertura:** `e2e/admin/admin-monitoring-case-follow-up.spec.js`.
