### FLOW: `admin-document-navigation`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/documents`
- **API:** `GET /api/documents/navigation/`, `GET/PATCH /api/accounts/panel-preferences/documents/`, `GET /api/documents/`, `GET /api/document-folders/`
- **Description:** El administrador recorre el gestor por proyecto o por cliente con el mismo interruptor y en la misma posición que Comunicaciones. Cada entrada muestra por separado cuántas carpetas y documentos tiene en el ámbito activo, archivado o combinado; el inventario incluye todo descendiente porque la asociación canónica está copiada en cada carpeta y documento. «Sin proyecto» y «Sin cliente» permanecen visibles incluso con cero elementos. La preferencia se guarda por cuenta, mientras `?by=` permite compartir una visita sin cambiar esa memoria. «Carpetas propias» conserva su árbol y sus acciones sin depender del eje elegido.
- **Steps:**
  1. El administrador entra al Gestor Documental y encuentra el interruptor Proyectos/Clientes encima de la navegación lateral.
  2. Recorre proyectos visibles; «Ver todos» recupera los que su estado excluye de la vista inicial.
  3. Elige un proyecto o «Sin proyecto» y el listado consulta únicamente esa asociación.
  4. Cambia a Clientes, elige una persona o «Sin cliente» y consulta su inventario.
  5. Sale del módulo y vuelve: el último modo elegido reaparece.
  6. Abre una carpeta propia antes o después del cambio de modo sin perder esa vía de organización.
- **Branches:**
  - [Branch A — Display] Cada entidad declara conteos separados de carpetas y documentos; clientes inactivos y proyectos ocultos con contenido siguen alcanzables.
  - [Branch B — Sin asignar] Las entradas «Sin proyecto»/«Sin cliente» existen permanentemente y filtran los registros sin esa asociación.
  - [Branch C — Memoria] Un cambio desde el interruptor hace `PATCH`; una visita posterior hidrata el modo mediante `GET`. Un `?by=` explícito sólo gobierna esa visita.
  - [Branch D — Carpetas propias] La sección manual no cambia al alternar el eje y sigue navegable si falla la carga de facetas.
  - [Branch E — Fallo recuperable] Un 5xx de `/documents/navigation/` muestra una explicación con «Reintentar» sin bloquear el resto del gestor.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-navigation.spec.js`
- **Unit Tests:** `test/components/FolderSidebar.spec.js`, `test/stores/document_navigation.test.js`, `test/composables/useDocumentFilterQuery.test.js`
- **Backend Tests:** `content/tests/views/test_document_navigation.py`, `accounts/tests/test_document_panel_preferences.py`
