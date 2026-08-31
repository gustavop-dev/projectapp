### FLOW: `admin-document-navigation`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/documents`
- **API:** `GET /api/documents/navigation/`, `GET/PATCH /api/accounts/panel-preferences/documents/`, `GET /api/documents/`, `GET /api/document-folders/`
- **Description:** El administrador recorre el gestor por proyecto o por cliente con el mismo interruptor y en la misma posición que Comunicaciones. El catálogo muestra por defecto sólo proyectos operativos —incluido PRUEBA aunque tenga inventario cero— y «Ver proyectos no activos» revela de forma inclusiva el grupo donde aparece Candle, sin ocultar los activos ni archivar sus documentos. Este control local de la visita es independiente de «Ver archivados», que cambia el ámbito de carpetas/documentos y se ubica justo antes de «Carpetas propias». Cada entrada muestra por separado cuántas carpetas y documentos tiene en el ámbito activo, archivado o combinado. «Sin proyecto» y «Sin cliente» permanecen visibles incluso con cero elementos. La preferencia se guarda por cuenta, mientras `?by=` permite compartir una visita sin cambiar esa memoria. «Carpetas propias» contiene exclusivamente raíces sin proyecto ni cliente; la conciliación es una tarea operativa interna y no genera avisos técnicos en esta navegación.
- **Steps:**
  1. El administrador entra al Gestor Documental y encuentra el interruptor Proyectos/Clientes encima de la navegación lateral.
  2. Recorre los proyectos operativos y activa «Ver proyectos no activos» cuando necesita consultar el grupo secundario; al apagarlo, cualquier proyecto que quede oculto devuelve la selección a «Todos».
  3. Elige un proyecto o «Sin proyecto» y el listado consulta únicamente esa asociación.
  4. Cambia a Clientes, elige una persona o «Sin cliente» y consulta su inventario.
  5. Sale del módulo y vuelve: el último modo elegido reaparece.
  6. Abre una carpeta sin asignar; la navegación limpia cualquier proyecto o cliente previamente seleccionado.
- **Branches:**
  - [Branch A — Display] Cada entidad declara conteos separados de carpetas y documentos; los proyectos no operativos están ocultos al entrar y aparecen, junto con los activos, sólo mientras su control inclusivo está encendido. Los clientes inactivos conservan su grupo secundario.
  - [Branch B — Sin asignar] Las entradas «Sin proyecto»/«Sin cliente» existen permanentemente y filtran los registros sin esa asociación.
  - [Branch C — Memoria] Un cambio desde el interruptor hace `PATCH`; una visita posterior hidrata el modo mediante `GET`. Un `?by=` explícito sólo gobierna esa visita.
  - [Branch D — Carpetas propias] La sección manual no cambia al alternar el eje, excluye raíces que ya tengan proyecto o cliente y sigue navegable si falla la carga de facetas.
  - [Branch E — Ejes excluyentes] Elegir proyecto limpia cliente, elegir cliente limpia proyecto y entrar a una carpeta manual limpia ambos; nunca se envían intersecciones accidentales.
  - [Branch F — Fallo recuperable] Un 5xx de `/documents/navigation/` muestra una explicación con «Reintentar» sin bloquear el resto del gestor.
  - [Branch G — Ámbitos independientes] «Ver proyectos no activos» no altera `scope`; «Ver archivados» sigue filtrando contenido activo/archivado en cualquier proyecto, cliente o carpeta propia.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-navigation.spec.js`
- **Unit Tests:** `test/components/FolderSidebar.spec.js`, `test/stores/document_navigation.test.js`, `test/composables/useDocumentFilterQuery.test.js`
- **Backend Tests:** `content/tests/views/test_document_navigation.py`, `accounts/tests/test_document_panel_preferences.py`
