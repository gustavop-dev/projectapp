### FLOW: `admin-document-title-column-resize`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents`
- **Description:** Permite distinguir documentos con títulos extensos sin abrirlos. En tabla y tarjetas, el título queda contenido en una línea con puntos suspensivos; si se recorta, incluso después de cargar las fuentes web, un único aviso flotante de la aplicación muestra el nombre completo y **Ver completo** permite expandirlo por foco, toque o clic con corte seguro incluso cuando no contiene espacios. El aviso usa el mismo `BaseTooltip` de las acciones de fila, se mantiene dentro del viewport y no convive con un `title` nativo duplicado. Los avisos breves de acciones usan una sola línea horizontal y también permanecen contenidos en el viewport; los textos descriptivos largos conservan su ajuste multilínea. La carpeta y los demás distintivos quedan ordenados debajo del título, sin reservar una línea vacía en las filas de escritorio que no tienen carpeta. En la tabla, la manija visible y etiquetada del encabezado **Título** ajusta el ancho entre 240 y el máximo de inventario de 520 px, recuerda la preferencia del navegador y vuelve a 320 px con doble clic.
- **Steps:**
  1. Admin abre **Gestor Documental** y consulta el listado.
  2. Un título recortado —con espacios o con guiones bajos— muestra un solo aviso flotante y **Ver completo**; uno que cabe no agrega información repetida.
  3. Pulsa **Ver completo** en la tabla o tarjeta y el título se despliega sin abrir el documento.
  4. Comprueba que la carpeta aparece debajo del título y que títulos, carpeta y metadatos permanecen dentro de la fila o tarjeta.
  5. En la tabla, arrastra la manija de **Título** o la opera con teclado para elegir el ancho.
  6. Recarga la página y el ancho elegido se conserva.
  7. Hace doble clic en la manija para recuperar el ancho predeterminado.
- **Branches:**
  - [Display — contención] Los nombres reales largos, incluidos los escritos sin espacios, permanecen dentro de su celda o tarjeta en celular, tableta y escritorio; nunca invaden Cliente ni otro contenido.
  - [Display — recorte] El aviso flotante y el control de expansión sólo existen cuando la medición del texto confirma recorte, incluida la remedición tras cargar fuentes web; el control de acciones reutiliza el mismo aviso sin sumar un `title` nativo y su etiqueta breve se lee horizontalmente dentro del viewport.
  - [Display — metadatos] Carpeta aparece primero en el renglón inferior; Cliente, Proyecto y Estado siguen allí cuando el perfil compacto los oculta como columnas. Sin carpeta, la tabla de escritorio conserva altura natural.
  - [Success — consulta] **Ver completo** expande el nombre en el mismo contexto con `overflow-wrap:anywhere`, y **Contraer** recupera la línea truncada.
  - [Success — reparto] Proyecto, Cliente y Fecha ceden espacio en ese orden; Estados y Acciones conservan su ancho.
  - [Success — límite] El máximo de 520 px cubre el nombre más largo del inventario productivo vigente; tras alcanzar los mínimos de las columnas flexibles, la tabla habilita desplazamiento horizontal interno.
  - [Success — restablecer] El doble clic elimina la preferencia guardada y devuelve Título a 320 px.
- **Coverage:** ✅ Covered (aviso flotante único para título y acción, nombre corto sin ruido, carga tardía de fuentes, límite del inventario vigente, nombres reales sin espacios, contención geométrica en cinco viewports, expansión táctil en tabla y galería, orden de metadatos, arrastre persistente, columnas fijas y restablecimiento).
- **E2E Spec:** `e2e/admin/admin-document-title-column-resize.spec.js`
