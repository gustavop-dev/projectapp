/**
 * Client plugin that auto-redirects first-time visitors to the appropriate
 * locale based on their browser language.
 *
 * - If browser language starts with 'es' → redirect to /es-co/
 * - Otherwise → stay on /en-us/ (current default)
 * - Manual locale switches (via LocaleSwitcher) are persisted in localStorage
 *   and always take precedence.
 * - Only fires on the main website routes (not /proposal/ or /panel/).
 */
export default defineNuxtPlugin((nuxtApp) => {
  const router = useRouter()

  router.afterEach((to) => {
    if (import.meta.server) return

    // Skip proposal and admin routes — they have their own language logic
    const path = to.path
    if (path.startsWith('/proposal') || path.startsWith('/panel')) return

    // If user already has a stored preference, respect it
    const STORAGE_KEY = 'preferred_locale'
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) return

    // Only redirect from the bare root or default-locale routes
    // If user is already on a locale-prefixed route, they chose it
    const isOnLocalePrefixed = path.startsWith('/es-co') || path.startsWith('/en-us')
    if (isOnLocalePrefixed) {
      // Mark as seen so we don't redirect again
      const currentLocale = path.startsWith('/es-co') ? 'es-co' : 'en-us'
      localStorage.setItem(STORAGE_KEY, currentLocale)
      return
    }

    // Detect browser language
    const browserLang = (navigator.language || navigator.languages?.[0] || '').toLowerCase()
    const isSpanish = browserLang.startsWith('es')
    const targetLocale = isSpanish ? 'es-co' : 'en-us'

    // Persist choice
    localStorage.setItem(STORAGE_KEY, targetLocale)

    // Redirect to locale-prefixed version of current path
    const targetPath = `/${targetLocale}${path === '/' ? '' : path}`
    router.replace(targetPath)
  })
})
