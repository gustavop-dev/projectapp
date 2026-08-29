### FLOW: `admin-client-communications`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/threads/`, `GET /api/communications/threads/:id/`, `POST /api/communications/threads/:id/messages/`, `/api/accounts/saved-filter-tabs/`
- **Description:** El administrador identifica varios hilos mediante resúmenes compactos y sin desplazamiento horizontal. Puede ordenar el listado y recuperar ese criterio en una visita posterior, recorrer las conversaciones por proyecto, cliente o «Sin proyecto», combinar filtros, guardar recortes propios y abrir el contenido completo en un modal de trabajo sin perder la lista. Cada hilo conserva mensajes entrantes o salientes con canal, fecha, estado y referencias a documentos existentes.
- **Steps:**
  1. El administrador entra a Comunicaciones desde el panel y navega por proyectos o clientes, con conteos que incluyen sus hilos.
  2. Identifica cada hilo por asunto, cliente, proyecto, canal, estado, cantidad, fecha y borradores; el último mensaje sólo aparece como extracto de una línea.
  3. Cambia entre recientes, antiguos o alfabético y recupera el criterio activo al volver al listado.
  4. Elige «Sin proyecto» cuando necesita consultar conversaciones todavía no asociadas a uno.
  5. Combina varios valores dentro de un filtro y, si reutiliza ese recorte, lo guarda con nombre como vista propia.
  6. Selecciona un hilo; el detalle se abre sobre la lista y muestra la línea de tiempo, sus estados y documentos referenciados.
  7. Escribe o pega el texto exacto y registra una salida como borrador o enviada, o una entrada como recibida.
  8. Cierra el detalle o vuelve atrás y recupera el mismo contexto de navegación y filtros.
- **Branches:**
  - [Branch A — Resumen compacto] En viewport angosto aparecen varias tarjetas identificables, el extracto ocupa una línea y no existe desplazamiento horizontal interno.
  - [Branch B — Orden persistente] El criterio elegido queda activo y vuelve a aplicarse en una visita posterior sin parámetro explícito en la URL.
  - [Branch C — Display] La navegación muestra proyectos, clientes y «Sin proyecto»; el modal presenta juntos lo enviado, lo recibido y los documentos referenciados.
  - [Branch D — Recorte guardado] La selección por cliente y los estados múltiples se guardan y se restauran como una vista propia.
  - [Branch E — Registro exitoso] Un mensaje saliente queda con estado `sent` y fecha explícita.
  - [Branch F — Error de negocio] La API rechaza el registro y el panel conserva el texto, mostrando la razón.
  - [Branch G — Fallo de carga] El listado no está disponible y el panel mantiene un reintento visible.
  - [Branch H — Alcance de canal] El aviso describe el registro manual vigente y puede cerrarse después de leído, sin prometer una fase posterior.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-client-communications.spec.js`
- **Unit Tests:** `test/components/CommunicationThreadTable.spec.js`, `test/composables/useCommunicationFilters.spec.js`, `test/stores/communications.test.js`
- **Backend Tests:** `content/tests/views/test_communication_views.py`, `content/tests/views/test_communication_filters.py`
