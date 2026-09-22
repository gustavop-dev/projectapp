# Personalizar la marca del Linktree

- **Rol:** admin. **Ruta:** `/panel/linktrees/:id/edit`.
- **Success:** editar colores/fuente, guardar y recargar conserva la apariencia;
  cargar una familia de Google Fonts la selecciona; subir/quitar logo actualiza la tarjeta.
- **Error:** una familia inexistente muestra error y conserva la selección.
- **Failure:** fallo de conexión a Google Fonts muestra aviso y permite reintentar.
- **Display:** entrar desde el listado muestra la apariencia y vista previa, también en móvil.
- **API:** PATCH de Linktree persiste colores y familia; POST/DELETE `logo/` guarda inmediatamente el logo independiente del avatar.
- **Cobertura:** `frontend/e2e/admin/admin-linktrees.spec.js` (API y Google Fonts simulados).
  Backend verifica persistencia real, serialización pública y rechazo de imágenes falsas.
