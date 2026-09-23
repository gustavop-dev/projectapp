# CAPTCHA en los inicios de sesión

Panel (`/admin/login/`) y Plataforma (`/platform/login`) exigen reCAPTCHA v2
Checkbox desde el primer intento. `/panel/login` conserva su enlace al Admin.
El backend valida el token antes de autenticar, crear sesión, emitir JWT o
enviar el OTP del primer acceso. El servicio compartido está en
`projectapp/recaptcha.py`; no se valida el token en recuperación, activación,
refresh de JWT ni intercambio administrativo de códigos de acceso.

Si falta el token o Google lo rechaza (incluidos expiración, reutilización y
hostname incorrecto), la plataforma devuelve 400 con `code` y `detail`.
Timeout, HTTP fallido, respuesta ilegible y configuración incompleta devuelven
503 `captcha_unavailable`. Django Admin muestra el mismo error en el formulario
sin crear sesión. El timeout HTTP es de 5 segundos; el script del navegador
espera hasta 10 segundos antes de ofrecer reintento. No hay fallback permisivo.
Cada intento fallido reinicia el widget; las sesiones abiertas no se invalidan.

## Configuración y activación

1. Registrar una clave de **reCAPTCHA v2 Checkbox** para cada ambiente y autorizar
   sus dominios exactos en Google. Producción: `projectapp.co` y
   `www.projectapp.co`; staging: su dominio real, sin comodines ni puertos.
2. Configurar fuera de git `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY` y
   `RECAPTCHA_ALLOWED_HOSTNAMES` (lista separada por comas).
3. Configurar `NUXT_PUBLIC_RECAPTCHA_SITE_KEY` con **la misma clave pública** del
   backend antes del build. Nunca exportar la clave secreta al frontend.
4. Ejecutar `manage.py check --deploy --tag security` en el entorno de despliegue;
   `projectapp.E001` bloquea una configuración incompleta o hostnames inválidos.
   Verificar también la igualdad de las claves públicas de backend/build.
5. Generar el frontend y desplegar backend/static de forma coordinada. No hay
   migraciones. Validar ambos formularios en staging con claves reales antes
   de promover el cambio: éxito, credenciales incorrectas, expiración y
   bloqueo de `google.com/recaptcha/api.js` con recuperación posterior.

`RECAPTCHA_ENABLED=false` permite desactivación explícita sólo en desarrollo y
tests. `settings_prod` lo fija a `True`, y `IS_PRODUCTION` también impide el
bypass. El frontend sólo admite `NUXT_PUBLIC_RECAPTCHA_ENABLED=false` en el
servidor de desarrollo; los builds generados exigen CAPTCHA. La falta de claves
deja el login cerrado, por lo que deben provisionarse antes de la activación.

## Pruebas aisladas

- pytest usa `settings_test` y CAPTCHA desactivado explícitamente para los tests
  de autenticación ordinarios. Los tests de CAPTCHA lo activan con claves
  ficticias y sustituyen únicamente el POST a Google.
- Jest verifica el widget, expiración, recuperación y carga compartida del
  script. Los tokens no se persisten en almacenamiento del navegador.
- `npx playwright test --config playwright.captcha.config.js panel-login-captcha.spec.js platform-login-captcha.spec.js`
  levanta Django en 3198 y Nuxt en 3199; usa `CAPTCHA_TEST_PYTHON` si el intérprete
  no es `python3`. El servidor comprueba settings/storage/cache aislados antes
  de crear una base SQLite temporal. No lee `.env` ni usa cuentas existentes.
- CI ejecuta estos recorridos en `login-captcha-tests`; las demás suites de
  Nuxt tienen una desactivación explícita limitada a su servidor de desarrollo.

Los logs de indisponibilidad registran sólo el motivo técnico, nunca tokens,
credenciales ni cuerpos de Google. Ante un pico de `captcha_unavailable`,
revisar conectividad, claves y dominios manteniendo el bloqueo. La validación
real con Google pertenece al despliegue; los tests automáticos son deterministas.
