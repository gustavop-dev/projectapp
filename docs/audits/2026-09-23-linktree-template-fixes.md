# Correcciones tras la revisión del PR #400

## Hallazgos reproducidos

- **Overlays fijos:** `body{position:fixed;inset:0}` y `main::before{content:"";position:fixed;inset:0}` pasaban la validación anterior a 320/375/430 px. La inspección omitía el propio `body` y las cajas de pseudoelementos.
- **Densidad de imágenes:** las variantes de un original de 600 px tenían todas 600 px, pero el HTML las anunciaba como 1x/2x/3x. Chromium reducía su ancho intrínseco a 200 px en DPR 3.
- **Despliegue:** el 23/09/2026 la ruta `/api/linktrees/admin/11111111-1111-4111-8111-111111111111/templates/` respondía 200 `text/html` con la portada. La API existente y `/api/health/` respondían desde Django. Esto prueba que la nueva ruta no está operativa; sin acceso al servidor no se determina si falta desplegar, reiniciar o corregir el proxy.

## Correcciones

1. Chromium inspecciona las cajas reales de layout mediante CDP, incluidos los elementos raíz y los pseudoelementos. Calcula el área que intersecta el viewport y muestrea fotogramas e intervalos intermedios de animaciones. Las decoraciones pequeñas o fuera de pantalla siguen permitidas. Una animación demasiado compleja bloquea la validación.
2. Los descriptores de densidad corresponden al tamaño real de las variantes, sin anunciar duplicados como densidades superiores. Los SVG usan una sola fuente. La lectura de publicaciones y vistas previas antiguas repara sólo los `srcset` generados por la plataforma, sin mutar el documento ni los datos guardados. La validación usa la misma reparación.
3. El deploy instala Chromium, prueba que arranque y exige que la ruta protegida de plantillas responda 401 JSON. Una portada HTML con 200 hace fallar el despliegue. El pull del deploy exige fast-forward. No se ejecutó el deploy desde el worktree.
4. CI instala Chromium en todos los shards que contienen pruebas de navegador de plantillas. Coverage registra los cambios de greenlet usados por Playwright.

## Evidencia local

- 13 pruebas Chromium de overlays y validación existente: aprobadas.
- 11 pruebas de imágenes, densidades, DPR 1/2/3 y documentos antiguos: aprobadas.
- 7 pruebas con servidor HTTP local para el comprobador de despliegue: aprobadas.
- Regresión adicional del inventario de correo: 4 casos aprobados. CI detectó un falso positivo al confundir `CDPSession.send` con SMTP; el guard ahora clasifica cada llamada y conserva el rechazo de SMTP incluso en la misma línea que el comando CDP.
- Quality gate estricto: aprobado para los archivos nuevos y el guard corregido; auditoría de los 25 casos iniciales: KEEP.
- `bash -n scripts/deploy.sh`: aprobado.
- Comprobación HTTP de producción con el nuevo script: **rechazada correctamente**, 200 HTML en la ruta de API.

No cambian rutas, formularios ni capacidades del frontend. Los flujos de cargar/validar/publicar/restablecer conservan su contrato; los nuevos casos verifican la geometría y recursos en el navegador del backend.

## Pendiente operativo

El código se entrega mediante un PR nuevo; la sesión no integra su propio PR. El despliegue y la comprobación final de producción requieren acceso al servidor. No se han aplicado migraciones ni cambiado servicios remotos.
