### FLOW: `admin-document-email-history`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/documents/:id/edit` → `/panel/emails?tab=history&email=:id`
- **Description:** El administrador ve los correos donde salió un documento y navega a la fila exacta del historial universal.
- **Interacciones y outcomes:**
  1. **display:** entrar al gestor, abrir un documento, leer **Este documento se envió en N correos** y comprobar asunto, destinatario, fecha y nombre archivado.
  2. **display:** pulsar una referencia y llegar al Historial con esa fila cargada y expandida.
  3. **success/error/failure:** n/a; es navegación de evidencia. La protección 409 al eliminar se cubre en integración backend.
- **E2E Spec:** `e2e/admin/admin-document-edit.spec.js`
