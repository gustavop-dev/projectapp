### FLOW: `admin-client-communications`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/threads/`, `GET /api/communications/threads/:id/`, `POST /api/communications/threads/:id/messages/`, `/api/accounts/saved-filter-tabs/`
- **Description:** El administrador identifica y busca varios hilos mediante resúmenes compactos, sin desplazamiento horizontal. Puede ordenar el listado y recuperar ese criterio, recorrer las conversaciones por proyecto, cliente o «Sin proyecto», ajustar la navegación lateral, combinar filtros, guardar recortes propios y abrir el contenido completo en un modal de trabajo sin perder la lista. Cada hilo conserva mensajes entrantes o salientes con canal, fecha, estado y referencias a documentos existentes.
- **Steps:**
  1. El administrador entra a Comunicaciones desde el panel y navega por proyectos o clientes, con conteos que incluyen sus hilos.
  2. Identifica cada hilo por asunto, cliente, proyecto, canal, estado, cantidad, fecha y borradores; el último mensaje sólo aparece como extracto de una línea.
  3. Cambia entre recientes, antiguos o alfabético y recupera el criterio activo al volver al listado.
  4. Elige «Sin proyecto» cuando necesita consultar conversaciones todavía no asociadas a uno.
  5. Busca por cliente, proyecto, asunto o contenido; combina varios valores dentro de un filtro y guarda el recorte con nombre cuando necesita reutilizarlo.
  6. Ajusta el ancho de la navegación para leer nombres largos y recupera ese ancho en otra visita.
  7. Selecciona un hilo; el detalle se abre sobre la lista y muestra la línea de tiempo, sus estados y documentos referenciados.
  8. Cierra el aviso del registro manual y puede reabrirlo desde la ayuda contextual.
  9. Escribe o pega el texto exacto y registra una salida como borrador o enviada, o una entrada como recibida.
  10. Cierra el detalle o vuelve atrás y recupera el mismo contexto de navegación y filtros.
- **Branches:**
  - [Branch A — Display] La navegación muestra proyectos, clientes y «Sin proyecto»; el modal presenta juntos lo enviado, lo recibido y los documentos referenciados.
  - [Branch B — Resumen compacto] En viewport angosto aparecen varias tarjetas identificables, el extracto ocupa una línea y no existe desplazamiento horizontal interno.
  - [Branch C — Orden persistente] El criterio elegido queda activo y vuelve a aplicarse en una visita posterior sin parámetro explícito en la URL.
  - [Branch D — Recorte guardado] La selección por cliente y los estados múltiples se guardan y se restauran como una vista propia.
  - [Branch E — Búsqueda por proyecto] El texto global consulta cliente, proyecto, asunto y contenido mediante el contrato REST/MCP compartido.
  - [Branch F — Alcance de canal] El aviso describe el registro manual vigente, conserva su cierre al recargar y puede reabrirse desde ayuda, sin prometer una fase posterior.
  - [Branch G — Navegación ajustable] El panel lateral conserva el ancho elegido y permite leer el nombre completo de un proyecto largo.
  - [Branch H — Registro exitoso] Un mensaje saliente queda con estado `sent` y fecha explícita.
  - [Branch I — Error de negocio] La API rechaza el registro y el panel conserva el texto, mostrando la razón.
  - [Branch J — Fallo de carga] El listado no está disponible y el panel mantiene un reintento visible.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-client-communications.spec.js`
- **Unit Tests:** `test/components/CommunicationThreadTable.spec.js`, `test/composables/useCommunicationFilters.spec.js`, `test/stores/communications.test.js`
- **Backend Tests:** `content/tests/views/test_communication_views.py`, `content/tests/views/test_communication_filters.py`
