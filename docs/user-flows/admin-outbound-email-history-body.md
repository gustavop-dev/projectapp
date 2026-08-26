### FLOW: `admin-outbound-email-history-body`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/emails?tab=history`
- **Description:** El administrador expande un correo de Seguridad y acceso y abre **Ver contenido completo**. El cuerpo retenido —incluidos OTP, invitaciones o credenciales— se carga por un endpoint administrativo y se muestra dentro de un iframe sandboxed, tal como advierte Configuración.
- **Interacciones y outcomes:**
  1. **display:** navegar al Historial, expandir una fila de Seguridad, abrir el visor y comprobar contenido real devuelto por la API dentro del iframe.
  2. **success:** n/a; la consulta no muta datos.
  3. **error:** el permiso se prueba en integración backend; una sesión no administrativa no puede alcanzar el panel.
  4. **failure:** el error de carga se presenta dentro del modal y se cubre en unidad/store; el E2E focal valida el cuerpo exitoso.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`
