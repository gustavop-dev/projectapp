### FLOW: `admin-monitoring-case-list`

- **Módulo / rol:** monitoreo / administrador del panel.
- **Ruta:** `/panel/monitoring` desde Monitoreo en la navegación.
- **Display:** casos de proyectos, identidad del recurso y salud de las fuentes.
- **Success:** cambiar a Servidores o aplicar filtros muestra la lista correspondiente, con paginación de 25.
- **Failure:** una carga fallida muestra un aviso y permite actualizar, sin simular una lista saludable.
- **API:** `GET /api/monitoring/catalog/`, `GET /api/monitoring/cases/`.
- **Cobertura:** `e2e/admin/admin-monitoring-case-list.spec.js`.
