### FLOW: `admin-document-project-readiness`

- **Module:** admin
- **Role:** superuser admin
- **Priority:** P2
- **Routes:** `/panel` → `/panel/documents`; actions lead to `/panel/projects`
- **Description:** La sección Proyectos del Gestor Documental consulta un diagnóstico independiente del árbol. Si faltan carpetas gestionadas, informa cuántas requieren la conciliación revisada sin convertirlas automáticamente. Si todos los proyectos están explícitamente excluidos del Gestor Documental, enlaza a Proyectos para revisarlos. Una falla del diagnóstico se muestra como error y no como un vacío normal.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-folders.spec.js`

| Interacción | Outcome | Inicio → pasos → resultado |
|---|---|---|
| Consultar una sección con raíces pendientes | display | Panel → Gestor Documental → se informa el número exacto pendiente y siguen visibles las raíces ya conciliadas. |
| Revisar un catálogo explícitamente excluido | success | Panel → Gestor Documental → Revisar proyectos → módulo de proyectos. |
| Fallar la consulta de diagnóstico | failure | Panel → Gestor Documental → respuesta 5xx → aviso de que no se pudo determinar la causa; nunca se presenta como ausencia real de proyectos. |
| Validación de entrada | error n/a | Es una consulta de solo lectura sin campos editables; permisos y sesión pertenecen a los flows de autenticación del panel. |
