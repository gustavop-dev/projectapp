# admin-pwa-install — Instalación del panel interno

- **Rol:** administrador. **Prioridad:** P2.
- **Entrada:** barra lateral o menú móvil de cualquier vista del panel.
- **Success:** pulsar Instalar ProjectApp, aceptar el diálogo y ocultar la oferta.
  Cancelarlo permite intentarlo después; cerrar la invitación persiste durante
  la sesión del navegador. La invitación solo aparece en el dashboard y no
  desplaza los datos de los módulos operativos.
- **Display:** abrir el menú móvil y la ayuda; consultar instrucciones del
  navegador y el requisito de conexión.
- **Failure:** el navegador rechaza el diálogo; mostrar ayuda y mensaje de error.
- **Error:** no aplica; no hay formulario ni nuevos permisos.
- **Specs:** `frontend/e2e/admin/admin-pwa-install.spec.js`. El diálogo del
  sistema operativo se simula en esa frontera; las interacciones del panel son reales.
- **Límite manual:** verificar el ícono instalado y la apertura standalone en
  dispositivos Chrome/Edge y Safari iOS; Playwright no acredita esa instalación nativa.
