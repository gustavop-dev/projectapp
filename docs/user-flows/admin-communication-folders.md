### FLOW: `admin-communication-folders`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/folders/`, `PATCH/DELETE /api/communications/folders/:id/`, `PATCH /api/communications/threads/:id/`
- **Description:** El administrador organiza hilos completos en carpetas y subcarpetas propias del cliente o proyecto; conserva el histórico y encuentra su ubicación tras recargar.
- **Steps:** Seleccionar cliente/proyecto → crear carpeta y subcarpeta → abrir hilo → Mover a carpeta → guardar → seleccionar carpeta → recargar → verificar ubicación e ID. Retirar mediante Sin carpeta.
- **Branches:**
  - **display:** árbol, ruta, subcarpetas e IDs legibles al navegar desde el panel.
  - **success:** crear/renombrar/mover carpeta, clasificar hilo abierto o cerrado y restaurar el filtro desde la URL.
  - **error:** rechazo al eliminar una carpeta con contenido o mover fuera del contexto.
  - **failure:** error de carga/escritura muestra feedback y permite reintentar sin simular éxito.
- **Invariants:** las comunicaciones madre permanecen en la raíz; un hilo conserva mensajes y adjuntos; los archivados impiden eliminar su carpeta; una búsqueda recorre todas las carpetas del contexto seleccionado.
- **Specs:** `frontend/e2e/admin/admin-communication-filing.spec.js`.
