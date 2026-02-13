/**
 * Client plugin that syncs @nuxtjs/i18n locale to the legacy language store.
 * This keeps legacy views working that depend on languageStore.currentLanguage,
 * languageStore.loadMessagesForView(), etc.
 */
import { watch } from 'vue'
import { useLanguageStore } from '~/stores/language'

export default defineNuxtPlugin(async (nuxtApp) => {
  try {
    const languageStore = useLanguageStore()
    const locale = (nuxtApp.$i18n as any)?.locale

    if (!locale) {
      console.warn('[language-sync] $i18n not available')
      return
    }

    const syncLocale = async (loc: string) => {
      const [language, region] = loc.split('-')
      languageStore.currentLocale = loc
      languageStore.currentLanguage = language
      languageStore.currentRegion = region || ''
      try {
        await languageStore.loadMessages(language)
      } catch (e) {
        console.warn('[language-sync] Failed to load messages:', e)
      }
    }

    await syncLocale(locale.value)

    watch(locale, (newLocale: string) => {
      syncLocale(newLocale)
    })
  } catch (e) {
    console.warn('[language-sync] Plugin init failed:', e)
  }
})
