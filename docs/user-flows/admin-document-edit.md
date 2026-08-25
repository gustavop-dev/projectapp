### FLOW: `admin-document-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/:id/edit`
- **Description:** Edita contenido, asociación cliente/proyecto, visibilidad en el portal y presentación de un documento. La entrada desde el gestor conserva carpeta, filtros, búsqueda, archivo, vista y página en un `from` interno validado; las salidas explícitas restauran ese contexto, mientras una entrada directa o no confiable vuelve a la raíz. La cabecera reserva el ancho de las acciones, limita el título a dos líneas y mantiene visibilidad/cliente sin empujar los controles; debajo muestra los estados concurrentes con su duración. **Acciones** contiene las salidas PDF y queda separado de **Cancelar/Guardar**. La asociación guardada ofrece backlinks y conserva el `client_name` heredado cuando no existe relación. La barra de Markdown permite copiar o pegar contenido. `doc-client-note-open` conserva los mensajes para el cliente, guarda esa metadata directamente y administra observaciones normalizadas enlazables con **Solucionar bug**. Nada de esta metadata aparece en el PDF ni en el portal del cliente.
- **Steps:**
  1. Admin llega desde el gestor a `/panel/documents/:id/edit` con su origen canónico en `from`; `GET /api/documents/:id/detail/` carga el documento.
  2. El formulario aparece precargado con título, contenido, visibilidad, asociación, configuración visual, episodios vigentes y notas privadas.
  3. Admin puede abrir **Ver notas**, **Editar notas** o **Agregar notas**, según el estado guardado.
  4. Revisa o modifica los mensajes, crea/edita/elimina notas personalizadas y pulsa **Guardar cambios**.
  5. `PATCH /api/documents/:id/update/` persiste sólo los tres mensajes y la lista completa `client_custom_notes`.
  6. El modal se cierra y la vista confirma **Notas guardadas**; cualquier otro cambio del editor continúa marcado como pendiente.
  7. Admin modifica o guarda por separado cualquier otro dato necesario.
- **Branches:**
  - [Display — lectura] Una cuenta de cobro emitida permite consultar y copiar todas sus notas, pero no crearlas, modificarlas ni eliminarlas.
  - [Display — volver] **Volver a documentos** y las demás salidas explícitas restauran la lista con su contexto y foco; el guard interviene si hay cambios sin guardar. Back del navegador conserva su semántica nativa y un `from` directo, externo o de otro módulo cae a la raíz localizada.
  - [Success — PDF] Preview y descarga usan la configuración guardada; **Acciones** permite descargar PDF Amigable o Profesional.
  - [Success — visibilidad] El interruptor persiste `is_client_visible` sin modificar el ciclo de trabajo.
  - [Success — estados] La administración de episodios y su historial se cubre en `admin-document-state-workflow`.
  - [Success — copiar Markdown] **Copiar** escribe todo `content_markdown` al portapapeles y muestra **Copiado** temporalmente.
  - [Success — pegar Markdown] **Pegar** inserta el texto en el cursor (o al final si no hay foco) y muestra **Pegado** temporalmente.
  - [Error — validación] Un rechazo 400 mantiene el modal abierto, conserva el borrador y muestra el error del campo.
  - [Failure — servidor] Un fallo 5xx mantiene el modal abierto con toda la colección editada para reintentar.
- **Coverage:** ✅ Covered (las notas privadas satisfacen display/success/error/failure; el retorno cubre salida explícita, Back nativo y fallback no confiable; asociaciones, Markdown, estilos, PDF y guard tienen cobertura propia o compartida en los specs).
- **E2E Spec:** `e2e/admin/admin-document-edit.spec.js`, `e2e/admin/admin-document-return-navigation.spec.js`
