### FLOW: `admin-document-state-workflow`

- **Módulo:** admin
- **Rol:** admin
- **Prioridad:** P1
- **Ruta:** `/panel/documents/:id/edit`
- **API:** `/api/documents/:id/state-episodes/`, `/api/documents/:id/state-history/`, `/api/documents/:id/notes/`
- **Descripción:** Un documento conserva un episodio por cada período en que tuvo un estado. El ciclo admite uno vigente y puede avanzar o volver; las señales se suman. Abrir, cerrar, quitar, corregir la fecha efectiva y repetir un estado dejan movimientos con fecha/hora y autor. **Cerrar** registra que el trabajo terminó; **quitar** registra que la marca no aplicaba. El historial muestra fecha exacta, tiempo relativo, duración, nota de cierre, autor y observaciones enlazadas.
- **Recorrido:** abrir un documento → seleccionar o crear al vuelo un estado → resolver sugerencias de nombres parecidos → registrar fecha real si aplica → cerrar o quitar desde un modal propio con nota opcional → consultar la línea de tiempo.
- **Observaciones:** crear una observación ofrece abrir **Solucionar bug**. Resolver o descartar la última observación pendiente cierra o quita automáticamente la señal enlazada; eliminar y restaurar se cubren en `admin-document-observation-delete`.
- **Ramas:**
  - [Display] El encabezado y el historial muestran episodios vigentes e históricos con duración y atribución.
  - [Success] Cambiar el ciclo cierra el episodio anterior; las señales permanecen concurrentes.
  - [Success] Una sugerencia reutiliza el estado global existente en lugar de duplicarlo.
  - [Error] Una incompatibilidad rechaza la combinación sin alterar los episodios actuales.
  - [Failure] Un cierre fallido deja el episodio abierto y visible.
- **Cobertura:** ✅ display/success/error/failure.
- **E2E:** `e2e/admin/admin-document-state-workflow.spec.js`
