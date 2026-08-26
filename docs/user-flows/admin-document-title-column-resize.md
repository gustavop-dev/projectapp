### FLOW: `admin-document-title-column-resize`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Routes:** `/panel/documents`
- **Description:** Permite distinguir documentos con títulos extensos sin abrirlos. El título ocupa hasta dos líneas; si el contenido realmente queda recortado, el navegador recibe el nombre completo como ayuda y aparece **Ver completo** para expandirlo dentro de la fila o tarjeta. En la tabla, la manija del encabezado **Título** ajusta el ancho entre 240 y 520 px, recuerda la preferencia del navegador y vuelve a 320 px con doble clic.
- **Steps:**
  1. Admin abre **Documentos PDF** y consulta el listado.
  2. Un título que supera dos líneas muestra la ayuda con su texto íntegro; uno que cabe no agrega información repetida.
  3. En celular o tableta vertical, pulsa **Ver completo** en la tarjeta y el título se despliega sin abrir el documento.
  4. En la tabla, arrastra la manija de **Título** o la opera con teclado para elegir el ancho.
  5. Recarga la página y el ancho elegido se conserva.
  6. Hace doble clic en la manija para recuperar el ancho predeterminado.
- **Branches:**
  - [Display — recorte] La ayuda y el control de expansión sólo existen cuando la medición del texto confirma desbordamiento.
  - [Success — táctil] **Ver completo** expande el nombre en el mismo contexto y **Contraer** recupera las dos líneas.
  - [Success — reparto] Etiquetas, Proyecto, Cliente y Fecha ceden espacio en ese orden; Estado y Acciones conservan su ancho.
  - [Success — límite] Tras alcanzar los mínimos de las columnas flexibles, la tabla habilita desplazamiento horizontal interno.
  - [Success — restablecer] El doble clic elimina la preferencia guardada y devuelve Título a 320 px.
- **Coverage:** ✅ Covered (recorte condicional, expansión compacta, arrastre persistente, columnas fijas y restablecimiento).
- **E2E Spec:** `e2e/admin/admin-document-title-column-resize.spec.js`
