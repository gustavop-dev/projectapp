# Marca y recursos del proyecto

- **Ruta/rol:** `/panel/projects`, admin, Acciones → Marca y recursos.
- **Success:** vincular/desvincular un Linktree conserva su URL pública; subir un archivo con nombre y categoría, descargarlo y eliminarlo previa confirmación.
- **Error:** carga rechazada conserva los campos y no añade un recurso.
- **Failure:** carga de biblioteca fallida muestra aviso y reintento.
- **Display:** abrir el modal desde el listado muestra los recursos o estados vacíos, también en móvil.
- **Cobertura:** `frontend/e2e/admin/admin-project-brand.spec.js`, API simulada; `backend/content/tests/views/test_project_brand.py` verifica persistencia, aislamiento, permisos y archivos privados reales.
