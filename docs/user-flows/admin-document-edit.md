### FLOW: `admin-document-edit`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/:id/edit`
- **Description:** Edita contenido, estado, asociación cliente/proyecto y presentación de un documento. La asociación guardada ofrece backlinks `document-client-link` y `document-project-link`; un `client_name` heredado se conserva como referencia mientras no exista relación. La barra de Markdown permite copiar todo el contenido o pegar en la posición del cursor. El selector Amigable/Profesional cambia el preview y el menú de descarga permite obtener cualquiera de los dos estilos. El acceso compacto `doc-client-note-open` abre un modal precargado con asunto del correo, cuerpo del correo y WhatsApp; aplicar cualquiera de esos cambios activa la protección de trabajo sin guardar. La nota no aparece en el PDF ni en el portal del cliente.
- **Steps:**
  1. Admin llega desde el gestor a `/panel/documents/:id/edit`; `GET /api/documents/:id/detail/` carga el documento.
  2. El formulario aparece precargado con título, contenido, estado, asociación, configuración visual y nota privada.
  3. Admin puede abrir **Ver nota**, **Editar nota** o **Agregar nota**, según el estado guardado.
  4. Revisa o modifica asunto, correo y WhatsApp, y pulsa **Aplicar al documento**.
  5. La vista marca la nota como **Sin guardar** y el aviso de cambios incluye los campos modificados.
  6. Admin modifica cualquier otro dato necesario y pulsa **Guardar cambios**.
  7. `PATCH /api/documents/:id/update/` persiste el documento y los tres valores exactos, y muestra confirmación.
- **Branches:**
  - [Display — lectura] Una cuenta de cobro emitida permite consultar y copiar una nota existente, pero no modificarla.
  - [Display — volver] **Volver a documentos** navega a la lista y el guard interviene si hay cambios sin guardar.
  - [Success — PDF] Preview y descarga usan la configuración guardada; el menú permite Amigable o Profesional.
  - [Success — estado] Cambiar draft/published/archived actualiza el estado persistido.
  - [Success — copiar Markdown] **Copiar** escribe todo `content_markdown` al portapapeles y muestra **Copiado** temporalmente.
  - [Success — pegar Markdown] **Pegar** inserta el texto en el cursor (o al final si no hay foco) y muestra **Pegado** temporalmente.
  - [Error — validación] Un rechazo 400 deja el aviso de cambios sin guardar y muestra el error del campo.
  - [Failure — servidor] Un fallo 5xx conserva el contenido editado dentro del modal para reintentar.
- **Coverage:** ✅ Covered (la nota privada satisface display/success/error/failure; asociaciones, Markdown, estilos, PDF y guard tienen cobertura propia o compartida en el spec).
- **E2E Spec:** `e2e/admin/admin-document-edit.spec.js`
