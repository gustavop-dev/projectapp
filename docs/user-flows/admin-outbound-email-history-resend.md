### FLOW: `admin-outbound-email-history-resend`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/emails?tab=history`
- **Description:** Reenvía desde el snapshot inmutable y permite cambiar sólo el destinatario; asunto, cuerpo y archivos permanecen bloqueados.
- **Interacciones y outcomes:**
  1. **success:** expandir un correo capturado, abrir **Reenviar exacto**, editar el destinatario y confirmar; el modal cierra y el panel confirma la nueva entrega.
  2. **failure:** si el SMTP rechaza el reenvío, el modal conserva el destinatario y muestra el error sin afirmar éxito.
  3. **error:** la validación de dirección inválida pertenece al contrato backend/input email y no amplía el cuerpo editable.
  4. **display:** el modal enumera el asunto y adjuntos bloqueados antes de confirmar.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`
