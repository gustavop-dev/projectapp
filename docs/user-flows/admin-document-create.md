### FLOW: `admin-document-create`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents/create`
- **Description:** Crea un documento desde Markdown pegado (con preview vivo) o cargado desde archivo. El bloque Identificación conserva la asociación opcional `ClientAutocomplete` (`doc-client-autocomplete`, con creación inline) + `ProjectSelect` (`doc-project-select`, `allowNoClient`): elegir primero el proyecto completa su cliente, elegir primero el cliente filtra los proyectos y limpiar el cliente limpia el proyecto. Una carpeta puede aportar su cliente/proyecto como valor heredado; sólo cuando no los declara se usa la sugerencia por mayoría estricta de documentos, siempre editable. El acceso compacto `doc-client-note-open` abre una nota privada que agrupa, en este orden, asunto del correo, cuerpo del correo y WhatsApp; no aparece en el PDF ni en el portal del cliente.
- **Steps:**
  1. Admin navega a `/panel/documents/create`.
  2. La vista ofrece **Pegar Markdown** y **Cargar Archivo**.
  3. Admin completa el título y, opcionalmente, cliente/proyecto en cualquier orden.
  4. Admin puede abrir **Agregar nota**, completar asunto, correo y WhatsApp, y pulsar **Aplicar al documento**; la vista principal sólo muestra el estado compacto de la nota.
  5. En **Pegar Markdown**, escribe o pega contenido y revisa el preview vivo; en **Cargar Archivo**, selecciona un `.md` y revisa el contenido cargado.
  6. Admin pulsa **Crear Documento**.
  7. `POST /api/documents/create-from-markdown/` recibe markdown, asociaciones, presentación y los tres campos privados (vacíos si se omitieron).
  8. Al guardar, admin navega al gestor de documentos.
- **Branches:**
  - [Display — nota] Cancelar cierra el modal sin aplicar el borrador; cada texto aplicado se puede copiar por separado.
  - [Display — preview] Admin puede mostrar u ocultar el panel de preview sin perder el markdown.
  - [Success — asociación] El payload siempre lleva `client`/`project`, incluido `null`; una asociación heredada o sugerida nunca bloquea la edición manual.
  - [Error — validación] Campos obligatorios faltantes o un rechazo 400 muestran errores y conservan al admin en la página de creación.
  - [Failure — servidor] Un fallo 5xx conserva la nota en el formulario para reintentar sin volver a redactarla.
- **Coverage:** ✅ Covered (paste, carga de archivo, asociaciones y nota privada en display/success/error/failure; las casillas de portada y el estilo viajan en el mismo payload, pero se auditan en sus flows específicos).
- **E2E Spec:** `e2e/admin/admin-document-create.spec.js`
