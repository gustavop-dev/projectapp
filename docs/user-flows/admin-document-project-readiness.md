### FLOW: `admin-document-project-readiness`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel` → `/panel/documents`; actions lead to `/panel/projects` or `/panel/projects/statuses`
- **Description:** La sección Proyectos del Gestor Documental consulta un diagnóstico independiente del árbol. Si faltan carpetas gestionadas, informa cuántas requieren la conciliación revisada PA-108 sin convertirlas automáticamente. Si ningún estado es visible, enlaza al catálogo de estados. Una falla del diagnóstico se muestra como error y no como un vacío normal.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-folders.spec.js`

| Interacción | Outcome | Inicio → pasos → resultado |
|---|---|---|
| Consultar una sección con raíces pendientes | display | Panel → Gestor Documental → se informa el número exacto pendiente y siguen visibles las raíces ya conciliadas. |
| Corregir un filtro de estados vacío | success | Panel → Gestor Documental → Administrar estados → catálogo de estados de proyecto. |
| Fallar la consulta de diagnóstico | failure | Panel → Gestor Documental → respuesta 5xx → aviso de que no se pudo determinar la causa; nunca se presenta como ausencia real de proyectos. |
| Validación de entrada | error n/a | Es una consulta de solo lectura sin campos editables; permisos y sesión pertenecen a los flows de autenticación del panel. |
