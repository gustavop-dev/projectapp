### FLOW: `admin-document-gallery`

- **Module:** admin
- **Role:** admin
- **Priority:** P2
- **Route:** `/panel/documents`
- **Description:** El gestor cambia de Lista a Galería y ve una tarjeta por documento con vista previa Markdown saneada, cliente, fecha, episodios de estado activos y un resumen `+N` cuando hay desborde. El botón de tres puntos abre la misma hoja de acciones de la lista, conserva `Acciones de <título>` como nombre accesible, no emite `title` nativo y muestra un único aviso breve `Acciones`.
- **Steps:** entrar a Documentos → elegir Galería → leer una tarjeta real → enfocar o posar el cursor sobre el botón de acciones y ver un solo aviso `Acciones` → abrir la hoja de acciones.
- **Branches:** las subcarpetas aparecen primero y aceptan arrastre; la preferencia de vista persiste; en móvil la galería es obligatoria y el toque abre la hoja sin depender de hover.
- **Coverage:** ✅ Display y apertura de acciones cubiertos.
- **E2E Spec:** `e2e/admin/admin-document-gallery.spec.js`
