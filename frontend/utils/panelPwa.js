import { computed, ref } from 'vue'

export const isPanelPath = (path) => /^\/(?:(?:es-co|en-us)\/)?panel(?:\/|$)/.test(path)

function installationBrowser(browser) {
  const { userAgent, maxTouchPoints } = browser.navigator
  if (/iPad|iPhone|iPod/i.test(userAgent) || (/Macintosh/i.test(userAgent) && maxTouchPoints > 1)) return 'ios'
  if (/Edg|Chrome|Chromium/i.test(userAgent)) return 'chromium'
  if (/Safari/i.test(userAgent)) return 'safari'
  return 'other'
}

/**
 * One controller per Nuxt app. The native event stays outside serialized state.
 * Without a browser this is an inert SSR instance, never shared between requests.
 */
export function createPanelPwa(browser) {
  const installed = ref(false)
  const isPrompting = ref(false)
  const instructionsOpen = ref(false)
  const installError = ref(false)
  const invitationVisible = ref(false)
  const browserKind = ref('other')
  const ready = ref(false)
  const canOffer = computed(() => ready.value && !installed.value)
  let deferredPrompt = null
  let invitationSeen = false
  let registration = null
  let cleanup = () => {}

  function dismissInvitation() {
    invitationVisible.value = false
  }

  function showInvitationOnce() {
    if (!canOffer.value || invitationSeen) return
    invitationSeen = true
    invitationVisible.value = true
    try { browser.sessionStorage.setItem('projectapp-pwa-invitation', 'seen') } catch { /* memory fallback */ }
  }

  async function install() {
    if (!canOffer.value || isPrompting.value) return
    installError.value = false
    dismissInvitation()
    const prompt = deferredPrompt
    if (!prompt) {
      instructionsOpen.value = true
      return
    }
    deferredPrompt = null
    isPrompting.value = true
    try {
      await prompt.prompt()
      const choice = await prompt.userChoice
      if (choice.outcome === 'accepted') installed.value = true
    } catch {
      installError.value = true
      instructionsOpen.value = true
    } finally {
      isPrompting.value = false
    }
  }

  async function registerWorker() {
    if (!ready.value || registration) return
    try {
      registration = browser.navigator.serviceWorker.register('/sw.js', { scope: '/', updateViaCache: 'none' })
      await registration
    } catch {
      registration = null // A later panel visit can retry without breaking navigation.
    }
  }

  function initialize() {
    if (!browser || ready.value || !browser.isSecureContext || !('serviceWorker' in browser.navigator)) return
    ready.value = true
    browserKind.value = installationBrowser(browser)
    const displayMode = browser.matchMedia('(display-mode: standalone)')
    function checkDisplayMode() {
      if (displayMode.matches || browser.navigator.standalone === true) {
        installed.value = true
        instructionsOpen.value = false
        dismissInvitation()
      }
    }
    function onPrompt(event) {
      if (!isPanelPath(browser.location.pathname)) return
      event.preventDefault()
      deferredPrompt = event
      installed.value = false
      checkDisplayMode()
    }
    function onInstalled() {
      installed.value = true
      deferredPrompt = null
      instructionsOpen.value = false
      dismissInvitation()
    }
    try { invitationSeen = browser.sessionStorage.getItem('projectapp-pwa-invitation') === 'seen' } catch { /* memory fallback */ }
    checkDisplayMode()
    browser.addEventListener('beforeinstallprompt', onPrompt)
    browser.addEventListener('appinstalled', onInstalled)
    displayMode.addEventListener?.('change', checkDisplayMode)
    cleanup = () => {
      browser.removeEventListener('beforeinstallprompt', onPrompt)
      browser.removeEventListener('appinstalled', onInstalled)
      displayMode.removeEventListener?.('change', checkDisplayMode)
    }
  }

  return {
    installed, canOffer, isPrompting, instructionsOpen, installError,
    invitationVisible, browserKind, initialize, install, registerWorker,
    showInvitationOnce, dismissInvitation, dispose: () => cleanup(),
  }
}
