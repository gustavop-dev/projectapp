### FLOW: `admin-client-communications`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/threads/`, `POST /api/communications/threads/tab-counts/`, `GET /api/communications/threads/:id/`, `POST /api/communications/threads/:id/messages/`, `/api/accounts/saved-filter-tabs/`, `POST /api/accounts/saved-filter-tabs/reset/`
- **Description:** El administrador identifica y busca varios hilos mediante resúmenes compactos, sin desplazamiento horizontal, y conserva el orden elegido entre visitas. Puede navegar por proyecto, cliente o «Sin proyecto», ajustar la navegación lateral, aplicar filtros prediseñados con conteos completos, combinar criterios y guardar recortes propios diferenciados. La tira se puede reordenar y restablecer sin borrar esas vistas; el contenido completo permanece en el detalle modal y cada hilo conserva mensajes entrantes o salientes con canal, fecha, estado y documentos referenciados.
- **Steps:**
  1. El administrador entra a Comunicaciones desde el panel y navega por proyectos o clientes en un panel ajustable, con conteos que incluyen sus hilos.
  2. Identifica cada hilo por asunto, cliente, proyecto, canal, estado, cantidad, fecha y borradores; el último mensaje sólo aparece como extracto de una línea.
  3. Cambia entre recientes, antiguos o alfabético y recupera el criterio activo al volver al listado.
  4. Elige «Sin proyecto» cuando necesita consultar conversaciones todavía no asociadas a uno y busca por cliente, proyecto, asunto o contenido.
  5. Elige de un clic un recorte prediseñado —primero «Borradores pendientes»— y consulta su conteo aunque sea cero; «Enviados sin respuesta» limita el resultado a hilos abiertos con salidas enviadas todavía no respondidas.
  6. Combina varios valores dentro de un filtro y guarda el recorte con nombre como vista propia, distinguida de las opciones de fábrica.
  7. Reordena la tira según su uso o restablece los prediseñados; las vistas propias permanecen disponibles.
  8. Ajusta el ancho de la navegación para leer nombres largos y recupera ese ancho en otra visita.
  9. Selecciona un hilo; el detalle se abre sobre la lista y muestra la línea de tiempo, sus estados y documentos referenciados.
  10. Cierra el aviso del registro manual y puede reabrirlo desde la ayuda contextual.
  11. Escribe o pega el texto exacto y registra una salida como borrador o enviada, o una entrada como recibida.
  12. Cierra el detalle o vuelve atrás y recupera el mismo contexto de navegación y filtros.
- **Branches:**
  - [Branch A — Display] La navegación muestra proyectos, clientes y «Sin proyecto»; el modal presenta juntos lo enviado, lo recibido y los documentos referenciados.
  - [Branch B — Resumen compacto] En viewport angosto aparecen varias tarjetas identificables, el extracto ocupa una línea y no existe desplazamiento horizontal interno.
  - [Branch C — Orden persistente] El criterio elegido queda activo y vuelve a aplicarse en una visita posterior sin parámetro explícito en la URL.
  - [Branch D — Conteos prediseñados] Todos los filtros de fábrica muestran su conteo, incluido cero.
  - [Branch E — Sin respuesta] El recorte aplica estado abierto, salida enviada y ausencia de respuesta.
  - [Branch F — Restablecimiento] La configuración restaura los prediseñados sin borrar ni alterar las vistas propias.
  - [Branch G — Recorte guardado] La selección por cliente y los estados múltiples se guardan y restauran como una vista identificada como «Propia».
  - [Branch H — Búsqueda] La consulta global encuentra por cliente, proyecto, asunto o contenido sin perder el alcance activo.
  - [Branch I — Alcance de canal] El aviso conserva su cierre al recargar y puede reabrirse desde ayuda.
  - [Branch J — Navegación ajustable] El panel lateral conserva el ancho elegido y permite leer nombres largos.
  - [Branch K — Registro exitoso] Un mensaje saliente queda con estado `sent` y fecha explícita.
  - [Branch L — Error de negocio] La API rechaza el registro y el panel conserva el texto, mostrando la razón.
  - [Branch M — Fallo de carga] El listado no está disponible y el panel mantiene un reintento visible.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-client-communications.spec.js`
- **Unit Tests:** `test/components/CommunicationThreadTable.spec.js`, `test/composables/useCommunicationFilters.spec.js`, `test/stores/communications.test.js`
- **Backend Tests:** `content/tests/views/test_communication_views.py`, `content/tests/views/test_communication_filters.py`
