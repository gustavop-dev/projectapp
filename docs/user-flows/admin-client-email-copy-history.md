### FLOW: `admin-client-email-copy-history`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/emails?tab=history` y los historiales compartidos de propuestas, diagnósticos, clientes y contabilidad.
- **Description:** El administrador expande el envío principal y ve debajo la lista **Copias internas (BCC)**. Cada intento muestra dirección, estado y, si falló sólo la copia, el error SMTP, sin convertirla en otra fila principal ni habilitar reintento.
- **Interacciones y outcomes:**
  1. **display:** navegar al historial, expandir un envío con datos reales y comprobar destinatario BCC, estado y error independiente.
  2. **success:** n/a; consultar la traza no muta datos.
  3. **error:** n/a; no hay entrada de usuario que validar en este bloque de lectura.
  4. **failure:** n/a como acción del usuario; el fallo SMTP de la copia es precisamente el dato persistido que cubre el outcome `display`.
- **E2E Spec:** `e2e/admin/admin-client-email-copy-settings.spec.js`
