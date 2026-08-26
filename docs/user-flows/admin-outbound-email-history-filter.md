### FLOW: `admin-outbound-email-history-filter`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/emails?tab=history`
- **Description:** El administrador llega desde la navegación del panel al Historial universal y acota las salidas por destinatario, familia, estado y rango de fechas; el servidor devuelve la fila principal coincidente sin limitar el resultado al compositor manual.
- **Interacciones y outcomes:**
  1. **display:** navegar a Emails, abrir Historial, completar los cuatro tipos de filtro y comprobar tanto los parámetros enviados como los datos reales de la fila resultante.
  2. **success:** n/a; filtrar no muta datos.
  3. **error:** n/a; los valores pertenecen a catálogos o controles de fecha y no existe una validación editable independiente.
  4. **failure:** la falla de carga se cubre en la frontera del store; esta interacción sólo registra la consulta exitosa con datos.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`
