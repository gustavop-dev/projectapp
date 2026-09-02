import { computed, watch } from 'vue'

import { usePersistedRef } from '~/composables/usePersistedRef'

export const ADDITIONAL_MODULES_THEME_STORAGE_KEY = 'projectapp-additional-modules-theme'

const THEMES = new Set(['light', 'dark'])

export function useAdditionalModulesTheme() {
  const persisted = usePersistedRef(
    ADDITIONAL_MODULES_THEME_STORAGE_KEY,
    'light',
    {
      serialize: (value) => value,
      deserialize: (value) => value,
    },
  )
  const theme = persisted.ref

  if (!THEMES.has(theme.value)) {
    theme.value = 'light'
    persisted.write('light')
  }

  watch(theme, (value) => {
    persisted.write(THEMES.has(value) ? value : 'light')
  }, { flush: 'sync' })

  const isDark = computed(() => theme.value === 'dark')

  function toggle() {
    theme.value = isDark.value ? 'light' : 'dark'
  }

  return { theme, isDark, toggle }
}
