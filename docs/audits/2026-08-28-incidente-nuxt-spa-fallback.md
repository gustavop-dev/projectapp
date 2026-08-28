# Incidente: bucle del fallback SPA de Nuxt

- **Fecha:** 2026-08-28
- **Servicio:** `projectapp.co` — panel administrativo
- **Severidad:** degradación funcional; servidor y API disponibles, panel no utilizable
- **Estado:** 🟡 mitigación implementada y verificada; cierre productivo pendiente de merge y deploy

## Resumen

Las rutas privadas del panel respondían HTTP 200, pero devolvían un documento de
101 bytes con un meta refresh hacia `/en-us/200.html`. Como esa ruta tampoco tenía
un archivo prerenderizado, Django volvía a entregar el mismo `200.html`. El
navegador repetía la navegación varias veces por segundo y nunca montaba Nuxt.

## Impacto y señal

- El panel, plataforma y demás rutas SPA no prerenderizadas podían quedar atrapadas
  en el mismo fallback.
- Gunicorn, Huey, socket, nginx y `/api/health/` permanecieron saludables.
- Los access logs mostraron solicitudes repetidas a rutas de panel y
  `/en-us/200.html`; no hubo una excepción backend que activara la healthcheck.
- La detección dependió del reporte humano porque el monitoreo validaba servicio/API,
  no el contenido de una ruta SPA profunda.

## Causa raíz

La actualización a Nuxt 4.5.2 y `@nuxtjs/i18n` 10.6 habilitó
`detectBrowserLanguage.redirectOn = 'no prefix'`. Nitro aplicó esa regla también a
su fallback especial `/200.html` y generó un redirect en lugar del shell SPA.
`serve_nuxt` cumplió su contrato técnico y sirvió el archivo existente, pero ningún
control comprobaba que ese archivo pudiera montar la aplicación.

## Corrección

1. Se deshabilitó la detección de idioma en Nuxt. Django ya decide el locale de la
   raíz mediante `preferred_locale` y el header `X-Country` de nginx.
2. Se añadió un validador de fallback que rechaza contenido vacío, meta refresh y
   documentos sin `#__nuxt`.
3. `build:django` ejecuta ese control antes de copiar o intercambiar el directorio
   publicado, por lo que conserva el build anterior si el nuevo artefacto es inválido.
4. Se añadieron regresiones unitarias y se mantuvieron los casos backend que sirven
   rutas anidadas del panel.

## Verificación

- Jest focal: 4/4 casos verdes.
- Pytest focal de `TestServeNuxtPanelRoute`: 3/3 casos verdes.
- `nuxi generate`: correcto; `200.html` válido de 8.235 bytes.
- `npm run build:django`: correcto; validación ejecutada antes del swap atómico.
- `npm audit`: 0 vulnerabilidades durante la instalación reproducible.

## Cierre pendiente

El protocolo por sesión prohíbe merge y deploy directos. Tras integrar y desplegar
el PR se debe verificar una ruta real de `/en-us/panel/**`: debe entregar un shell
con `#__nuxt`, sin `http-equiv="refresh"`, cargar sus chunks y dejar de producir la
ráfaga de accesos. Como acción preventiva adicional, la healthcheck debe inspeccionar
ese contenido para detectar futuras regresiones aunque la API siga saludable.
