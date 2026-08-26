### FLOW: `admin-document-list`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Route:** `/panel/documents`
- **Description:** El gestor conserva título, cliente, proyecto, estados vigentes con duración, fecha y acciones. El ciclo aparece primero y las señales después; **Solucionar bug** se distingue como acción pendiente y un desborde se resume en `+N`. En 412 px y 835 px el árbol de carpetas pasa a un drawer con foco contenido y el documento se presenta como tarjeta. Desde 1195 px vuelve la estructura de dos zonas; la tabla agrupa sus columnas secundarias antes de `panel-desktop` (1280 px) y las recupera en anchos mayores. En 2560 px el contenido completo queda centrado con un máximo de 1400 px.
- **Steps:** entrar desde la navegación del panel → leer un documento real → abrir o usar el árbol de carpetas → acceder a las acciones de la fila/tarjeta → cambiar entre activos, archivados y todos.
- **Branches:** un nombre largo de carpeta sigue legible dentro del drawer; el modo archivado conserva su franja; por debajo de 1280 px cliente, proyecto y estados se agrupan dentro de la celda principal; ningún ancho produce scroll horizontal de página.
- **Coverage:** ✅ Display responsivo cubierto en 412×915, 835×1194, 1195×835, 1440×900 y 2560×1440.
- **E2E Specs:** `e2e/admin/admin-document-list.spec.js`, `e2e/admin/admin-responsive-documents-clients-projects.spec.js`
