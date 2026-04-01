import { ref } from 'vue'

const STORAGE_KEY = 'platform_theme'
const isDark = ref(false)

export function usePlatformTheme() {
  function hydrate() {
    if (typeof window === 'undefined') return
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'light') {
      isDark.value = false
    } else if (stored === 'dark') {
      isDark.value = true
    } else {
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
  }

  function toggle() {
    isDark.value = !isDark.value
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
    }
  }

  return { isDark, toggle, hydrate }
}
