### FLOW: `admin-proposal-change-history`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/proposals/:id/edit`
- **Description:** Abre Historial en una propuesta; consulta precio y alcance por versión, compara versiones o la última enviada correctamente y consulta su evidencia.
- **Display outcome:** Navegar desde la interfaz hasta un registro real y verificar sus cambios, autor y fecha. Evidencia incompleta se identifica sin inventar versiones; el estado vacío explica la ausencia de datos anteriores.
- **Success outcome:** Consultar precio y alcance históricos y comparar una versión con la última enviada correctamente.
- **Error outcome:** n/a — los controles emiten sólo identificadores y opciones válidas. Permisos, pertenencia y validación del contrato se prueban en backend.
- **Failure outcome:** Fallos de API muestran una recuperación explícita y no revelan valores protegidos ni comparaciones obsoletas.
- **Coverage:** Display, success y failure validados en `admin/admin-entity-history.spec.js`.
