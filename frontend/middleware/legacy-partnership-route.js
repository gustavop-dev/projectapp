export default defineNuxtRouteMiddleware((to) => {
  // This boundary match cannot rewrite unrelated financing-guide URLs.
  const path = to.path.replace(
    /^\/(en-us\/|es-co\/)?panel\/financing(?=\/|$)/,
    (_match, locale) => `/${locale || 'es-co/'}panel/partnership-program`,
  )
  if (path === to.path) return
  return navigateTo({ path, query: to.query, hash: to.hash }, { replace: true, redirectCode: 301 })
})
