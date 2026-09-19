import { createPanelPwa, isPanelPath } from '~/utils/panelPwa'

export default defineNuxtPlugin((nuxtApp) => {
  const controller = createPanelPwa(window)
  controller.initialize()
  const route = useRoute()

  // The manifest belongs to the internal panel; public linktrees keep their
  // existing independent installation UI.
  useHead(() => ({
    link: isPanelPath(route.path) ? [
      { rel: 'manifest', href: '/manifest.webmanifest' },
      { rel: 'apple-touch-icon', href: '/img/icons/icon-logo-192x192.png' },
    ] : [],
    meta: isPanelPath(route.path) ? [
      { name: 'theme-color', content: '#002921' },
      { name: 'apple-mobile-web-app-capable', content: 'yes' },
      { name: 'apple-mobile-web-app-title', content: 'ProjectApp' },
    ] : [],
  }))

  function preparePanel() {
    if (!isPanelPath(route.path)) return
    if (!import.meta.dev) controller.registerWorker()
  }
  nuxtApp.hook('app:mounted', preparePanel)
  nuxtApp.hook('page:finish', preparePanel)
  if (import.meta.hot) import.meta.hot.dispose(() => controller.dispose())
  return { provide: { panelPwa: controller } }
})
