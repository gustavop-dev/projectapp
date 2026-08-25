### FLOW: `admin-document-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/:id/edit`
- **Description:** Edita contenido, asociación cliente/proyecto, visibilidad en el portal y presentación de un documento. La cabecera reserva primero el ancho de las acciones: en 412×915 y 835×1195 las coloca debajo del título, y desde 1024 px usa una columna no reducible. El título admite hasta dos líneas con su valor completo en `title`; visibilidad y cliente comparten una línea secundaria sin empujar las acciones. Debajo aparecen los estados concurrentes con su duración, mientras la barra lateral permite administrarlos. **Acciones** contiene las salidas PDF y queda separado del par **Cancelar/Guardar**, cuyas etiquetas nunca se parten. La asociación guardada ofrece backlinks `document-client-link` y `document-project-link`; un `client_name` heredado se conserva como referencia mientras no exista relación. La barra de Markdown permite copiar o pegar contenido. El acceso compacto `doc-client-note-open` conserva los mensajes para el cliente y administra observaciones normalizadas enlazables con **Solucionar bug**. Nada de esta metadata aparece en el PDF ni en el portal del cliente.
- **Steps:**
  1. Admin llega desde el gestor a `/panel/documents/:id/edit`; `GET /api/documents/:id/detail/` carga el documento.
  2. El formulario aparece precargado con título, contenido, visibilidad, asociación, configuración visual, episodios vigentes y notas privadas.
  3. Admin puede abrir **Ver notas**, **Editar notas** o **Agregar notas**, según el estado guardado.
  4. Revisa o modifica los mensajes, crea/edita/elimina notas personalizadas y pulsa **Aplicar al documento**.
  5. La vista marca las notas como **Sin guardar** y el aviso de cambios incluye los campos modificados.
  6. Admin modifica cualquier otro dato necesario y pulsa **Guardar cambios**.
  7. `PATCH /api/documents/:id/update/` persiste el documento, los tres mensajes y la lista completa `client_custom_notes`, y muestra confirmación.
- **Branches:**
  - [Display — lectura] Una cuenta de cobro emitida permite consultar y copiar todas sus notas, pero no crearlas, modificarlas ni eliminarlas.
  - [Display — volver] **Volver a documentos** navega a la lista y el guard interviene si hay cambios sin guardar.
  - [Success — PDF] Preview y descarga usan la configuración guardada; **Acciones** permite descargar PDF Amigable o Profesional.
  - [Success — visibilidad] El interruptor persiste `is_client_visible` sin modificar el ciclo de trabajo.
  - [Success — estados] La administración de episodios y su historial se cubre en `admin-document-state-workflow`.
  - [Success — copiar Markdown] **Copiar** escribe todo `content_markdown` al portapapeles y muestra **Copiado** temporalmente.
  - [Success — pegar Markdown] **Pegar** inserta el texto en el cursor (o al final si no hay foco) y muestra **Pegado** temporalmente.
  - [Error — validación] Un rechazo 400 deja el aviso de cambios sin guardar y muestra el error del campo.
  - [Failure — servidor] Un fallo 5xx conserva toda la colección editada dentro del modal para reintentar.
- **Coverage:** ✅ Covered (las notas privadas satisfacen display/success/error/failure; asociaciones, Markdown, estilos, PDF y guard tienen cobertura propia o compartida en el spec).
- **E2E Spec:** `e2e/admin/admin-document-edit.spec.js`
