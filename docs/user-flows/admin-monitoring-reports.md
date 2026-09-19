### FLOW: `admin-monitoring-reports`

- **Módulo / rol:** monitoreo / administrador del panel.
- **Ruta:** `/panel/monitoring`, pestaña Reportes.
- **Display:** reportes informativos y aviso de retención de 90 días.
- **Success:** abrir un reporte presenta texto plano, sin controles de seguimiento de casos.
- **Failure:** una carga fallida se comunica y permite volver a intentar.
- **API:** `GET /api/monitoring/reports/` y `GET /api/monitoring/reports/:id/`.
- **Cobertura:** `e2e/admin/admin-monitoring-case-list.spec.js`.
