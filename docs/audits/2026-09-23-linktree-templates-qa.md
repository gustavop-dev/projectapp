# QA de plantillas HTML de Linktree — 2026-09-23

Rama: `feat/23092026-linktree-html-templates`, base `main`, [PR #400](https://github.com/gustavop-dev/projectapp/pull/400). Trabajo en worktree; sin cambios en producción ni migraciones sobre una base real.

## Alcance y evidencia

- Backend: 16 casos de paquetes/render, 6 de auditoría en Chromium y 16 de API/servicio. Prueban rechazo de contenido ejecutable, rutas externas, ZIP fuera de alcance, recursos gráficos, expansión de bucles, contraste, objetivos táctiles, movimiento, permisos, aislamiento por cliente, estados de publicación e instantáneas inmutables.
- Frontend unitario: 10 casos del editor, store y runtime. Cubren carga/publicación, recuperación de errores, protección frente a respuestas tardías, portapapeles, vCard, clics e instalación.
- E2E: cinco casos con API simulada y acciones reales de UI; la validación del servidor tiene su propia cobertura backend. Los cinco pasaron en CI (run `35814598171`, artefacto `coverage-frontend-e2e/playwright-results.json`). El primer intento local perdió la conexión IPC de Nuxt dev; no se alteraron las comprobaciones para ocultar ese fallo.
- Quality gate focal: 9 archivos, 46 definiciones, 0 errores, 6 avisos. Semántica estricta, junk como error y linters externos ejecutados. La auditoría manual dictaminó KEEP: los avisos corresponden a lectura de capturas temporales, selectores semánticos del contrato del runtime.
- Regresiones: contratos MCP y fake data, 20 verificaciones de catálogos, comprobación de migraciones sin diferencias; mapa de vistas (115 entradas), contrato responsivo y registro de flows consistentes.

Los flows modificados `admin-linktree-templates` (success/error/failure/display) y `public-linktree-view` (success/display/failure) tienen evidencia estructural para sus resultados. El audit general mantiene brechas ajenas al cambio: 31 flows parciales y un junk-only preexistente (`platform-hosting-subscription`). No se modificaron pruebas de otros módulos para alterar esos resultados.

## Ejecución y límites

Se ejecutaron sólo lotes focalizados, de hasta 20 casos por comando. pytest usó `projectapp.settings_test`, SQLite y almacenamiento temporal. No se regeneraron datos de una base compartida. El helper del toolkit no está instalado en este host: se usaron los scripts versionados del repositorio y agentes QA de arquitectura, autoría, verificación, auditoría y corrección. No hay herramienta de mutation testing configurada.

CI detectó una diferencia al agregar metadatos: html5lib conserva `<` dentro de atributos entre comillas por defecto. La corrección activa `escape_lt_in_attrs=True` y conserva la aserción contra HTML de perfil sin escapar.

La compilación local inicial agotó el heap de 2 GB de Node durante el prerender. Para este checkout se repite con `NODE_OPTIONS=--max-old-space-size=4096`, sin cambiar la configuración del servicio. Un timeout de navegación en el responsive de recuperación de contraseña de Plataforma es ajeno a este cambio y no motivó cambios en ese módulo.

El estado vigente de CI y la entrega del commit final se verifican en el PR. Requisitos de despliegue y decisiones del contrato: [guía de plantillas](../LINKTREE_HTML_TEMPLATES.md).
