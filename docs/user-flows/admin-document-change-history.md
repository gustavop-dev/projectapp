### FLOW: `admin-document-change-history`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/documents/:id/edit`
- **Description:** Abre Historial desde el detalle del documento; consulta versiones completas y campos modificados, compara dos versiones o la anterior, invierte el orden y pagina.
- **Display outcome:** Navegar desde la interfaz hasta un registro real y verificar sus cambios, autor y fecha. Evidencia incompleta se identifica sin inventar versiones; el estado vacío explica la ausencia de datos anteriores.
- **Success outcome:** Consultar el contenido completo, comparar dos versiones o la anterior e invertir el orden o paginar la cronología.
- **Error outcome:** n/a — los controles emiten sólo identificadores y opciones válidas. Permisos, pertenencia y validación del contrato se prueban en backend.
- **Failure outcome:** Fallos de API muestran una recuperación explícita y no revelan valores protegidos ni comparaciones obsoletas.
- **Coverage:** Display, success y failure validados en `admin/admin-entity-history.spec.js`.
