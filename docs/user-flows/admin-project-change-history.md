### FLOW: `admin-project-change-history`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/projects`
- **Description:** Abre el detalle de accesos y su pestaña Historial; consulta URLs, notas y credenciales enmascaradas, revela un secreto por acción explícita y lo oculta al cerrar.
- **Display outcome:** Navegar desde la interfaz hasta un registro real y verificar sus cambios, autor y fecha. Evidencia incompleta se identifica sin inventar versiones; el estado vacío explica la ausencia de datos anteriores.
- **Success outcome:** Consultar una versión histórica de accesos, revelar una credencial por acción explícita y ocultarla al terminar la consulta.
- **Error outcome:** n/a — los controles emiten sólo identificadores y opciones válidas. Permisos, pertenencia y validación del contrato se prueban en backend.
- **Failure outcome:** Fallos de API muestran una recuperación explícita y no revelan valores protegidos ni comparaciones obsoletas.
- **Coverage:** Display, success y failure validados en `admin/admin-entity-history.spec.js`.
