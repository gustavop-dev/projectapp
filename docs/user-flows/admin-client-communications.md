### FLOW: `admin-client-communications`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/threads/`, `GET /api/communications/threads/:id/`, `POST /api/communications/threads/:id/messages/`
- **Description:** El administrador conserva el recorrido de una conversación sin convertirla en documento. Un hilo pertenece a un cliente, puede apuntar a un proyecto y contiene mensajes entrantes o salientes con canal, fecha, estado y referencias a documentos existentes. En esta primera fase la plataforma registra; no envía realmente por correo ni WhatsApp.
- **Steps:**
  1. El administrador abre Comunicaciones y consulta los hilos filtrables.
  2. Selecciona un hilo y lee los mensajes en orden temporal junto con canal, dirección y estado.
  3. Escribe o pega el texto exacto de una comunicación.
  4. Registra una salida como borrador o enviada, o una entrada como respuesta recibida.
  5. La línea de tiempo se vuelve a consultar y muestra el nuevo registro.
- **Branches:**
  - [Branch A — Consulta] La línea de tiempo muestra juntos lo enviado, lo recibido y los documentos referenciados.
  - [Branch B — Registro exitoso] Un mensaje saliente queda con estado `sent` y fecha explícita.
  - [Branch C — Error de negocio] La API rechaza el registro y el panel conserva el texto, mostrando la razón.
  - [Branch D — Fallo de carga] El listado no está disponible y el panel muestra un estado de error visible.
  - [Branch E — Alcance de canal] El aviso superior aclara que copiar/enviar ocurre fuera de la plataforma en esta fase.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-client-communications.spec.js`
- **Unit Tests:** `test/stores/communications.test.js`
- **Backend Tests:** `content/tests/views/test_communication_views.py`
