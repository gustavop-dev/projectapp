### FLOW: `admin-client-change-history`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/clients`
- **Description:** Expande un cliente y abre Ver historial de cambios; consulta identidad, contacto y facturación con autor y fecha; pagina y compara versiones.
- **Display outcome:** Navegar desde la interfaz hasta un registro real y verificar sus cambios, autor y fecha. Evidencia incompleta se identifica sin inventar versiones; el estado vacío explica la ausencia de datos anteriores.
- **Success outcome:** Consultar contacto y facturación de una versión, comparar cambios e invertir la cronología.
- **Error outcome:** n/a — los controles emiten sólo identificadores y opciones válidas. Permisos, pertenencia y validación del contrato se prueban en backend.
- **Failure outcome:** Fallos de API muestran una recuperación explícita y no revelan valores protegidos ni comparaciones obsoletas.
- **Coverage:** Display, success y failure validados en `admin/admin-entity-history.spec.js`.
