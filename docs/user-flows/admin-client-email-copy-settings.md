### FLOW: `admin-client-email-copy-settings`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/emails?tab=defaults`
- **Description:** El administrador abre **Emails → Configuración** y gestiona una lista de copias universales separada de los destinatarios de avisos internos. La pantalla declara que la copia es BCC, advierte que cada destinatario aumenta el volumen SMTP y de bandeja, avisa que Seguridad incluye OTP/credenciales cuyo cuerpo pueden consultar los administradores, y permite segmentar cada dirección en ocho familias: Propuestas, Diagnósticos, Documentos y comunicaciones, Cuentas de cobro, Contabilidad, Plataforma, Tareas y operación y Seguridad y acceso.
- **Interacciones y outcomes:**
  1. **display:** navegar desde el panel, abrir Configuración y ver dirección, estado, ocho familias, modo BCC y advertencias de volumen/seguridad con los datos reales de la respuesta.
  2. **success:** agregar una dirección, cambiar sus familias, pausarla/reactivarla o eliminarla; cada acción persiste por su endpoint propio y actualiza la fila.
  3. **error:** intentar agregar un duplicado o guardar una selección inválida muestra el detalle de validación del backend.
  4. **failure:** un fallo 5xx al mutar conserva el estado anterior y muestra que la operación no se completó.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`
