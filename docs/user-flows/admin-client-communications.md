### FLOW: `admin-client-communications`

- **Module:** admin
- **Role:** admin
- **Priority:** P1
- **Routes:** `/panel/communications`
- **API:** `GET/POST /api/communications/threads/`, `POST /api/communications/threads/tab-counts/`, `GET /api/communications/threads/:id/`, `POST /api/communications/threads/:id/messages/`, `/api/accounts/saved-filter-tabs/`, `POST /api/accounts/saved-filter-tabs/reset/`
- **Description:** El administrador recorre y busca el registro manual de conversaciones por proyecto, por cliente o por la entrada explícita «Sin proyecto». Puede ajustar la navegación lateral, aplicar filtros prediseñados con conteos completos, combinar criterios y guardar recortes propios diferenciados. La tira se puede reordenar y restablecer sin borrar esas vistas propias. El detalle se abre en un modal de trabajo sin perder la lista y cada hilo conserva mensajes entrantes o salientes con canal, fecha, estado y referencias a documentos existentes.
- **Steps:**
  1. El administrador entra a Comunicaciones desde el panel y navega por proyectos o clientes en un panel ajustable, con conteos que incluyen sus hilos.
  2. Elige «Sin proyecto» cuando necesita consultar conversaciones todavía no asociadas a uno.
  3. Busca por cliente, proyecto, asunto o contenido.
  4. Elige de un clic un recorte prediseñado —primero «Borradores pendientes»— y consulta su conteo aunque sea cero; «Enviados sin respuesta» limita el resultado a hilos abiertos con salidas enviadas todavía no respondidas.
  5. Combina varios valores dentro de un filtro y, si reutiliza ese recorte, lo guarda con nombre como vista propia, distinguida de las opciones de fábrica.
  6. Reordena la tira según su uso o restablece los prediseñados; las vistas propias permanecen disponibles.
  7. Selecciona un hilo; el detalle se abre sobre la lista y muestra la línea de tiempo, sus estados y documentos referenciados.
  8. Escribe o pega el texto exacto y registra una salida como borrador o enviada, o una entrada como recibida.
  9. Cierra el detalle o vuelve atrás y recupera el mismo contexto de navegación y filtros.
- **Branches:**
  - [Branch A — Display] La navegación muestra proyectos, clientes y «Sin proyecto», conserva el ancho elegido y permite leer nombres largos; el modal presenta juntos lo enviado, lo recibido y los documentos referenciados.
  - [Branch B — Búsqueda] La consulta global encuentra por cliente, proyecto, asunto o contenido sin perder el alcance activo.
  - [Branch C — Prediseñados] Todos los filtros de fábrica muestran su conteo, incluido cero, y el activo permanece accesible; el recorte «Enviados sin respuesta» aplica estado abierto, salida enviada y ausencia de respuesta.
  - [Branch D — Recorte guardado] La selección por cliente y los estados múltiples se guardan y se restauran como una vista propia, identificada como «Propia».
  - [Branch E — Restablecimiento] La configuración devuelve la tira de fábrica a su orden original sin borrar ni alterar las vistas propias.
  - [Branch F — Registro exitoso] Un mensaje saliente queda con estado `sent` y fecha explícita.
  - [Branch G — Error de negocio] La API rechaza el registro y el panel conserva el texto, mostrando la razón.
  - [Branch H — Fallo de carga] El listado no está disponible y el panel mantiene un reintento visible.
  - [Branch I — Alcance de canal] El aviso describe el registro manual vigente, conserva su cierre al recargar y puede reabrirse desde ayuda, sin prometer una fase posterior.
- **Coverage:** ✅ Covered
- **E2E Spec:** `e2e/admin/admin-client-communications.spec.js`
- **Unit Tests:** `test/stores/communications.test.js`
- **Backend Tests:** `content/tests/views/test_communication_views.py`, `content/tests/views/test_communication_filters.py`
