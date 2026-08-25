### FLOW: `admin-document-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/:id/edit`
- **Description:** Edita contenido, estado, asociación cliente/proyecto y presentación de un documento. La entrada desde el gestor lleva el contexto completo de carpeta, filtros, búsqueda, archivo, vista y página en un `from` interno validado; las salidas explícitas lo restauran y enfocan el documento de origen, mientras una entrada directa o no confiable vuelve a la raíz. La cabecera reserva primero el ancho de las acciones: en 412×915 y 835×1195 las coloca debajo del título, y desde 1024 px usa una columna no reducible. El título admite hasta dos líneas con su valor completo en `title`; estado y cliente comparten una línea secundaria sin empujar las acciones. **Acciones** contiene las salidas PDF y queda separado del par **Cancelar/Guardar**, cuyas etiquetas nunca se parten. La asociación guardada ofrece backlinks `document-client-link` y `document-project-link`; un `client_name` heredado se conserva como referencia mientras no exista relación. La barra de Markdown permite copiar todo el contenido o pegar en la posición del cursor. El selector Amigable/Profesional cambia el preview y el menú de descarga permite obtener cualquiera de los dos estilos. El acceso compacto `doc-client-note-open` abre **Notas**, precargado con asunto, correo, WhatsApp y notas adicionales ordenadas con título/contenido; **Guardar cambios** persiste sólo esa metadata y no deja un segundo guardado pendiente. Nada de esta metadata aparece en el PDF ni en el portal del cliente.
- **Steps:**
  1. Admin llega desde el gestor a `/panel/documents/:id/edit` con su origen canónico en `from`; `GET /api/documents/:id/detail/` carga el documento.
  2. El formulario aparece precargado con título, contenido, estado, asociación, configuración visual y notas privadas.
  3. Admin puede abrir **Ver notas**, **Editar notas** o **Agregar notas**, según el estado guardado.
  4. Revisa o modifica los mensajes, crea/edita/elimina notas personalizadas y pulsa **Guardar cambios**.
  5. `PATCH /api/documents/:id/update/` persiste sólo los tres mensajes y la lista completa `client_custom_notes`.
  6. El modal se cierra y la vista confirma **Notas guardadas**; cualquier otro cambio del editor continúa marcado como pendiente.
  7. Admin modifica o guarda por separado cualquier otro dato necesario.
- **Branches:**
  - [Display — lectura] Una cuenta de cobro emitida permite consultar y copiar todas sus notas, pero no crearlas, modificarlas ni eliminarlas.
  - [Display — volver] **Volver a documentos** y las demás salidas explícitas restauran la lista con su contexto y foco; el guard interviene si hay cambios sin guardar. Back del navegador conserva su semántica nativa y un `from` directo, externo o de otro módulo cae a la raíz localizada.
  - [Success — PDF] Preview y descarga usan la configuración guardada; **Acciones** permite descargar PDF Amigable o Profesional.
  - [Success — estado] Cambiar draft/published/archived actualiza el estado persistido.
  - [Success — copiar Markdown] **Copiar** escribe todo `content_markdown` al portapapeles y muestra **Copiado** temporalmente.
  - [Success — pegar Markdown] **Pegar** inserta el texto en el cursor (o al final si no hay foco) y muestra **Pegado** temporalmente.
  - [Error — validación] Un rechazo 400 mantiene el modal abierto, conserva el borrador y muestra el error del campo.
  - [Failure — servidor] Un fallo 5xx mantiene el modal abierto con toda la colección editada para reintentar.
- **Coverage:** ✅ Covered (las notas privadas satisfacen display/success/error/failure; el retorno cubre salida explícita, Back nativo y fallback no confiable; asociaciones, Markdown, estilos, PDF y guard tienen cobertura propia o compartida en los specs).
- **E2E Spec:** `e2e/admin/admin-document-edit.spec.js`, `e2e/admin/admin-document-return-navigation.spec.js`
