### FLOW: `admin-document-title-column-resize`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents`
- **Description:** Permite distinguir documentos con títulos extensos sin abrirlos. En tabla y tarjetas, el título queda contenido en una línea con puntos suspensivos; si se recorta, el navegador recibe el nombre completo como ayuda y aparece **Ver completo** para expandirlo con corte seguro incluso cuando no contiene espacios. La carpeta y los demás distintivos quedan ordenados debajo del título, sin reservar una línea vacía en las filas de escritorio que no tienen carpeta. En la tabla, la manija del encabezado **Título** ajusta el ancho entre 240 y 520 px, recuerda la preferencia del navegador y vuelve a 320 px con doble clic.
- **Steps:**
  1. Admin abre **Gestor Documental** y consulta el listado.
  2. Un título recortado —con espacios o con guiones bajos— muestra la ayuda y **Ver completo**; uno que cabe no agrega información repetida.
  3. Pulsa **Ver completo** en la tabla o tarjeta y el título se despliega sin abrir el documento.
  4. Comprueba que la carpeta aparece debajo del título y que títulos, carpeta y metadatos permanecen dentro de la fila o tarjeta.
  5. En la tabla, arrastra la manija de **Título** o la opera con teclado para elegir el ancho.
  6. Recarga la página y el ancho elegido se conserva.
  7. Hace doble clic en la manija para recuperar el ancho predeterminado.
- **Branches:**
  - [Display — contención] Los nombres reales largos, incluidos los escritos sin espacios, permanecen dentro de su celda o tarjeta en celular, tableta y escritorio; nunca invaden Cliente ni otro contenido.
  - [Display — recorte] La ayuda y el control de expansión sólo existen cuando la medición del texto confirma recorte.
  - [Display — metadatos] Carpeta aparece primero en el renglón inferior; Cliente, Proyecto y Estado siguen allí cuando el perfil compacto los oculta como columnas. Sin carpeta, la tabla de escritorio conserva altura natural.
  - [Success — consulta] **Ver completo** expande el nombre en el mismo contexto con `overflow-wrap:anywhere`, y **Contraer** recupera la línea truncada.
  - [Success — reparto] Proyecto, Cliente y Fecha ceden espacio en ese orden; Estados y Acciones conservan su ancho.
  - [Success — límite] Tras alcanzar los mínimos de las columnas flexibles, la tabla habilita desplazamiento horizontal interno.
  - [Success — restablecer] El doble clic elimina la preferencia guardada y devuelve Título a 320 px.
- **Coverage:** ✅ Covered (nombres reales sin espacios, contención geométrica en cinco viewports, recorte condicional, expansión en tabla y galería, orden de metadatos, arrastre persistente, columnas fijas y restablecimiento).
- **E2E Spec:** `e2e/admin/admin-document-title-column-resize.spec.js`
