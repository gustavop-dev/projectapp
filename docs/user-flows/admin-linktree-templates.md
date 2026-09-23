# Plantillas HTML del Linktree

- **Flow:** `admin-linktree-templates`
- **Rol:** admin · **Prioridad:** P1
- **Ruta:** `/panel/linktrees/:id/edit` → Apariencia → Plantilla HTML.
- **Superficies:** `LinktreeTemplateEditor.vue`, store `linktree-templates.js`, API `linktree_template.py` y servicios `linktree_templates/`.

| Outcome | Interacciones que deben comprobarse |
| --- | --- |
| success | Seleccionar ZIP/archivos/carpeta, subir y esperar validación; publicar la candidata válida; aplicar plantilla compartida; reemplazar/restablecer un asset; restaurar una versión y publicar; volver al tema básico conservando historial. |
| error | Paquete inválido con archivo/línea; resultado visual inválido que bloquea publicación; perfil cambiado desde validación; imagen no editable o formato incompatible. |
| failure | Biblioteca/API no disponible con reintento; error recuperable de cola/Chromium; versión expirada; recursos o Google Fonts inaccesibles. |
| display | Entrar desde el listado, abrir editor y elegir ancho; comprobar iframe sandbox, las tres capturas, estado y versiones; bloqueo explicado si hay datos sin guardar o validación pendiente. |

El ámbito de compartición es el cliente del proyecto. Las pruebas backend comprueban el aislamiento entre clientes y los permisos de sesión/CSRF; los E2E comprueban el recorrido observable del editor y sus respuestas de API. Las mediciones reales de Chromium pertenecen a `test_linktree_template_browser.py`.

La ruta pública mantiene `public-linktree-view`: con `template_url` carga el HTML publicado; la ruta localizada de Django aplica CSP antes de entregar el documento. Los enlaces y acciones se verifican con una plantilla fixture controlada, sin depender de los identificadores internos `data-template-node`.

Selectores estables: `template-file-input`, `template-upload-validate`, `template-library-select`, `template-validating`, `template-valid`, `template-publish`, `template-revalidate`, `template-share`, `template-asset-<key>`, `template-issues`, `template-sandbox-preview`, `template-screenshots`, `template-version-select`, `template-restore`, `template-reset`.
