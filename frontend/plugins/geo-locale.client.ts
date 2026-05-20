/**
 * Client plugin que persiste el locale elegido por el usuario.
 *
 * La decisión inicial de idioma para visitantes nuevos la toma el servidor:
 * Django redirige la raíz `/` a `/es-co/` o `/en-us/` según el país del
 * visitante (header `X-Country` de geoip2) — ver `backend/projectapp/views.py`.
 *
 * Este plugin sincroniza la preferencia en `localStorage` y en la cookie
 * `preferred_locale`, de modo que un cambio manual de idioma quede persistido
 * y el redirect server-side de Django lo respete en visitas futuras.
 *
 * - Solo actúa sobre las rutas del sitio público (no `/proposal/` ni `/panel/`).
 * - En rutas sin prefijo de locale (caso raro) cae a `navigator.language`.
 */
export default defineNuxtPlugin(() => {
  const router = useRouter()

  const STORAGE_KEY = 'preferred_locale'

  function persistLocale(locale: string) {
    localStorage.setItem(STORAGE_KEY, locale)
    // Cookie legible por Django para el redirect server-side de la raíz.
    document.cookie = `${STORAGE_KEY}=${locale}; path=/; max-age=31536000; samesite=lax`
  }

  router.afterEach((to) => {
    if (import.meta.server) return

    // Skip proposal and admin routes — they have their own language logic
    const path = to.path
    if (path.startsWith('/proposal') || path.startsWith('/panel')) return

    const isOnLocalePrefixed = path.startsWith('/es-co') || path.startsWith('/en-us')
    if (isOnLocalePrefixed) {
      // Sincroniza la preferencia con el locale actual. Captura tanto el
      // primer aterrizaje como los cambios manuales vía el switcher.
      const currentLocale = path.startsWith('/es-co') ? 'es-co' : 'en-us'
      persistLocale(currentLocale)
      return
    }

    // Ruta sin prefijo de locale: respeta una preferencia previa si existe.
    if (localStorage.getItem(STORAGE_KEY)) return

    // Fallback: detectar por idioma del navegador.
    const browserLang = (navigator.language || navigator.languages?.[0] || '').toLowerCase()
    const targetLocale = browserLang.startsWith('es') ? 'es-co' : 'en-us'
    persistLocale(targetLocale)

    const targetPath = `/${targetLocale}${path === '/' ? '' : path}`
    router.replace(targetPath)
  })
})
