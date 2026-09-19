import { computed, getCurrentInstance, inject, provide, watch } from 'vue'
import { usePersistedRef } from '~/composables/usePersistedRef'

/** Share a page's local theme with its viewer without changing the panel or
 * other public pages. A standalone panel preview owns its own theme. */
export function usePublicDocumentTheme(storageKey) {
  const contextKey = `public-document-theme:${storageKey}`
  const instance = getCurrentInstance()
  const inherited = instance ? inject(contextKey, null) : null
  if (inherited) return inherited

  const persisted = usePersistedRef(storageKey, 'light', {
    serialize: (value) => value,
    deserialize: (value) => value,
  })
  const theme = persisted.ref
  if (!['light', 'dark'].includes(theme.value)) {
    theme.value = 'light'
    persisted.write('light')
  }
  watch(theme, (value) => persisted.write(value), { flush: 'sync' })
  const isDark = computed(() => theme.value === 'dark')
  const state = {
    theme,
    isDark,
    toggle: () => { theme.value = isDark.value ? 'light' : 'dark' },
  }
  if (instance) provide(contextKey, state)
  return state
}
