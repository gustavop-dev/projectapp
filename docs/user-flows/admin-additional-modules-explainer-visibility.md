### FLOW: `admin-additional-modules-explainer-visibility`

- **Módulo:** admin
- **Rol:** admin
- **Prioridad:** P2
- **Ruta:** `/:locale/panel/additional-modules`
- **Interacción:** Encender o apagar "Mostrar el video a los clientes" junto a
  la tarjeta compacta del video. El cambio se guarda al instante, se confirma
  con un aviso y agenda el rebuild de la página pública; si el guardado falla,
  el interruptor vuelve a su estado anterior y se avisa el error. El
  interruptor sigue visible con el panel en inglés.
- **Outcomes:** `success`, `failure`
- **Evidencia:** `ExplainerVisibilityToggle.vue`, `stores/explainer_videos.js`,
  `PATCH explainer-videos/admin/settings/update/` y
  `e2e/admin/admin-additional-modules.spec.js`.
