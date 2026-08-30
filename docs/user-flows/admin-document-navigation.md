### FLOW: `admin-document-navigation`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/documents`
- **API:** `GET /api/documents/navigation/`, `GET/PATCH /api/accounts/panel-preferences/documents/`, `GET /api/documents/`, `GET /api/document-folders/`
- **Description:** El administrador recorre el gestor por proyecto o por cliente con el mismo interruptor y en la misma posición que Comunicaciones. El catálogo incluye todas las entidades habilitadas aunque tengan cero contenido y separa los proyectos fuera de operación en «Proyectos archivados» y los clientes inactivos en su propio grupo, sin archivar sus documentos. Cada entrada muestra por separado cuántas carpetas y documentos tiene en el ámbito activo, archivado o combinado. «Sin proyecto» y «Sin cliente» permanecen visibles incluso con cero elementos. La preferencia se guarda por cuenta, mientras `?by=` permite compartir una visita sin cambiar esa memoria. «Carpetas sin asignar» contiene exclusivamente raíces sin proyecto ni cliente.
- **Steps:**
  1. El administrador entra al Gestor Documental y encuentra el interruptor Proyectos/Clientes encima de la navegación lateral.
  2. Recorre proyectos activos y el grupo abierto de proyectos archivados; ambos incluyen registros con inventario cero.
  3. Elige un proyecto o «Sin proyecto» y el listado consulta únicamente esa asociación.
  4. Cambia a Clientes, elige una persona o «Sin cliente» y consulta su inventario.
  5. Sale del módulo y vuelve: el último modo elegido reaparece.
  6. Abre una carpeta sin asignar; la navegación limpia cualquier proyecto o cliente previamente seleccionado.
- **Branches:**
  - [Branch A — Display] Cada entidad declara conteos separados de carpetas y documentos; clientes inactivos y proyectos no operativos siguen alcanzables en grupos secundarios, incluso con cero contenido.
  - [Branch B — Sin asignar] Las entradas «Sin proyecto»/«Sin cliente» existen permanentemente y filtran los registros sin esa asociación.
  - [Branch C — Memoria] Un cambio desde el interruptor hace `PATCH`; una visita posterior hidrata el modo mediante `GET`. Un `?by=` explícito sólo gobierna esa visita.
  - [Branch D — Carpetas sin asignar] La sección manual no cambia al alternar el eje, excluye raíces que ya tengan proyecto o cliente y sigue navegable si falla la carga de facetas.
  - [Branch E — Ejes excluyentes] Elegir proyecto limpia cliente, elegir cliente limpia proyecto y entrar a una carpeta manual limpia ambos; nunca se envían intersecciones accidentales.
  - [Branch F — Fallo recuperable] Un 5xx de `/documents/navigation/` muestra una explicación con «Reintentar» sin bloquear el resto del gestor.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-navigation.spec.js`
- **Unit Tests:** `test/components/FolderSidebar.spec.js`, `test/stores/document_navigation.test.js`, `test/composables/useDocumentFilterQuery.test.js`
- **Backend Tests:** `content/tests/views/test_document_navigation.py`, `accounts/tests/test_document_panel_preferences.py`
