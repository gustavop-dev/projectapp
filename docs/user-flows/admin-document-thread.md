### FLOW: `admin-document-thread`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Route:** `/panel/documents`, `/panel/documents/:id/edit`
- **API:** `GET /api/documents/:id/thread/`, `GET /api/document-threads/candidates/`, `GET/POST /api/document-threads/`, `PATCH/DELETE /api/document-threads/:id/`
- **Description:** El administrador forma una historia cronológica con documentos ubicados en cualquier carpeta, cliente o proyecto. Cada documento puede pertenecer a un solo hilo y la relación se consulta desde un espacio de trabajo con pestañas para asignación, detalle y cronología.
- **Steps:**
  1. El administrador abre las acciones de un documento y elige «Hilo de documentos», usa el indicador del editor, hace clic en el badge «Hilo · N» de la lista, o entra por «Hilos» y elige uno del índice.
  2. En «Relacionar» asigna un nombre, busca documentos por título, carpeta, cliente o proyecto y define la fecha de cada hito.
  3. Guarda al menos dos documentos; el listado muestra «Hilo · N» y el modal abre luego en «Cronología».
  4. Selecciona un hito para consultar su contenido markdown o su PDF en «Detalle».
- **Branches:**
  - [Branch A — Display] La cronología ordena por fecha ascendente y conserva la posición relativa cuando dos fechas coinciden; los archivados siguen visibles con su estado.
  - [Branch B — Success] El hilo puede cruzar carpetas, clientes y proyectos; renombrar, cambiar fechas o miembros actualiza la misma relación.
  - [Branch C — Error] Todo candidato bloqueado se explica: el ocupado por otro hilo nombra ese hilo y su tamaño, y el ya agregado al borrador lo dice también; el conflicto 409 mantiene el modal abierto con una explicación.
  - [Branch F — Index] «Hilos» enumera los hilos con búsqueda, orden (reciente, último hito, A–Z) y rango de fechas, y abre cada uno por su primer miembro; sin hilos explica cómo crear el primero.
  - [Branch D — Failure] Un fallo al consultar el hilo conserva el espacio de trabajo y presenta el error sin inventar una relación vacía.
  - [Branch E — Lifecycle] Archivar conserva la membresía, eliminar se bloquea hasta retirar el documento y dejar un solo miembro disuelve el hilo con confirmación.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-document-thread.spec.js`
- **Unit Tests:** `test/components/DocumentThreadModal.spec.js`, `test/components/DocumentThreadIndexModal.spec.js`, `test/stores/document_threads.test.js`, `test/components/DocumentActionsSheet.spec.js`, `test/components/DocumentsTable.spec.js`, `test/components/DocumentCard.spec.js`
- **Backend Tests:** `content/tests/services/test_document_thread_service.py`, `content/tests/views/test_document_thread_views.py`
