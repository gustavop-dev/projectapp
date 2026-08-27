### FLOW: `admin-document-observation-delete`

- **Módulo:** admin
- **Rol:** admin
- **Prioridad:** P1
- **Ruta:** `/panel/documents/:id/edit`
- **API:** `/api/documents/:id/notes/`, `/api/documents/:id/notes/bulk-delete/`, `/api/documents/:id/notes/:note_id/restore/`, `/api/documents/:id/notes/events/`
- **Descripción:** **Descartar** conserva una observación real y el motivo por el que no se atendió. **Eliminar** limpia una prueba, duplicado o error: la observación desaparece de la lista y de los conteos, pero queda recuperable en la papelera. La confirmación muestra el contenido completo y recuerda que una copia enviada por correo o mensaje no se borra fuera del sistema. La actividad conserva solamente quién eliminó o restauró y cuándo, sin duplicar el contenido.
- **Recorrido:** abrir un documento → abrir **Notas** → elegir una observación de cualquier estado → **Eliminar** → revisar contenido y advertencia → confirmar → revisar la papelera o restaurar. Para limpieza, seleccionar varias y confirmar una sola operación atómica.
- **Coherencia:** si la última observación pendiente de un episodio originado por observaciones se elimina, **Solucionar bug** deja de estar activo. Restaurarla reabre o reutiliza el estado compatible; un conflicto cancela toda la restauración.
- **Ramas:**
  - [Display] Cancelar conserva la observación; la confirmación explica eliminación, recuperación y copias externas.
  - [Display] La actividad identifica actor y fecha sin mostrar el contenido eliminado.
  - [Success] Eliminar la última pendiente limpia la señal originada por observaciones.
  - [Success] El borrado masivo envía una sola selección atómica y la restauración devuelve una observación desde la papelera.
  - [Failure] Un fallo mantiene la confirmación y el contenido visibles para reintentar o cancelar.
- **Cobertura:** ✅ display/success/failure.
- **E2E:** `e2e/admin/admin-document-observation-delete.spec.js`
