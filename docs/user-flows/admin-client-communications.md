### FLOW: `admin-client-communications`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/threads/`, `GET /api/communications/threads/:id/`, `POST /api/communications/threads/:id/messages/`, `/api/accounts/saved-filter-tabs/`
- **Description:** El administrador recorre y busca el registro manual de conversaciones por proyecto, por cliente o por la entrada explícita «Sin proyecto». Puede ajustar la navegación lateral, combinar filtros, guardar recortes propios y abrir el detalle en un modal de trabajo sin perder la lista. Cada hilo conserva mensajes entrantes o salientes con canal, fecha, estado y referencias a documentos existentes.
- **Steps:**
  1. El administrador entra a Comunicaciones desde el panel y navega por proyectos o clientes, con conteos que incluyen sus hilos.
  2. Elige «Sin proyecto» cuando necesita consultar conversaciones todavía no asociadas a uno.
  3. Busca por cliente, proyecto, asunto o contenido; combina varios valores dentro de un filtro y, si reutiliza ese recorte, lo guarda con nombre como vista propia.
  4. Selecciona un hilo; el detalle se abre sobre la lista y muestra la línea de tiempo, sus estados y documentos referenciados.
  5. Escribe o pega el texto exacto y registra una salida como borrador o enviada, o una entrada como recibida.
  6. Cierra el detalle o vuelve atrás y recupera el mismo contexto de navegación y filtros.
- **Branches:**
  - [Branch A — Display] La navegación muestra proyectos, clientes y «Sin proyecto»; el modal presenta juntos lo enviado, lo recibido y los documentos referenciados.
  - [Branch B — Recorte guardado] La selección por cliente y los estados múltiples se guardan y se restauran como una vista propia.
  - [Branch C — Registro exitoso] Un mensaje saliente queda con estado `sent` y fecha explícita.
  - [Branch D — Error de negocio] La API rechaza el registro y el panel conserva el texto, mostrando la razón.
  - [Branch E — Fallo de carga] El listado no está disponible y el panel mantiene un reintento visible.
  - [Branch F — Alcance de canal] El aviso describe el registro manual vigente, conserva su cierre al recargar y puede reabrirse desde ayuda, sin prometer una fase posterior.
  - [Branch G — Navegación ajustable] El panel lateral conserva el ancho elegido y permite leer el nombre completo de un proyecto largo.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-client-communications.spec.js`
- **Unit Tests:** `test/stores/communications.test.js`
- **Backend Tests:** `content/tests/views/test_communication_views.py`, `content/tests/views/test_communication_filters.py`
