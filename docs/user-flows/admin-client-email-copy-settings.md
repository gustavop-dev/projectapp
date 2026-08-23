### FLOW: `admin-client-email-copy-settings`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/emails?tab=defaults`
- **Description:** El administrador abre **Emails → Configuración** y gestiona una lista de copias a clientes separada de los destinatarios de avisos contables. La pantalla declara que la copia es BCC, advierte que cada destinatario aumenta el volumen SMTP y de bandeja, y permite segmentar cada dirección por Propuestas, Diagnósticos, Documentos y correos manuales, Cuentas de cobro y Plataforma.
- **Interacciones y outcomes:**
  1. **display:** navegar desde el panel, abrir Configuración y ver dirección, estado, familias, modo BCC y advertencia de volumen con los datos reales de la respuesta.
  2. **success:** agregar una dirección, cambiar sus familias, pausarla/reactivarla o eliminarla; cada acción persiste por su endpoint propio y actualiza la fila.
  3. **error:** intentar agregar un duplicado o guardar una selección inválida muestra el detalle de validación del backend.
  4. **failure:** un fallo 5xx al mutar conserva el estado anterior y muestra que la operación no se completó.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`

