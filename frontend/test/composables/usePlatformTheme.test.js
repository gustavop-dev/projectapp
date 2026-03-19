/**
 * Tests for usePlatformTheme composable.
 *
 * Covers: hydrate (stored dark, stored light, system preference fallback),
 * toggle (dark→light, light→dark, persistence).
 */

const STORAGE_KEY = 'platform_theme'

let usePlatformTheme

describe('usePlatformTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()
    const mod = require('../../composables/usePlatformTheme')
    usePlatformTheme = mod.usePlatformTheme
  })

  describe('hydrate', () => {
    it('sets dark mode when stored value is dark', () => {
      localStorage.setItem(STORAGE_KEY, 'dark')
      const { hydrate, isDark } = usePlatformTheme()

      hydrate()

      expect(isDark.value).toBe(true)
    })

    it('sets light mode when stored value is light', () => {
      localStorage.setItem(STORAGE_KEY, 'light')
      const { hydrate, isDark } = usePlatformTheme()

      hydrate()

      expect(isDark.value).toBe(false)
    })

    it('falls back to system preference when no stored value', () => {
      window.matchMedia = jest.fn().mockReturnValue({ matches: false })
      const { hydrate, isDark } = usePlatformTheme()

      hydrate()

      expect(isDark.value).toBe(false)
      expect(window.matchMedia).toHaveBeenCalledWith('(prefers-color-scheme: dark)')
    })

    it('detects dark system preference', () => {
      window.matchMedia = jest.fn().mockReturnValue({ matches: true })
      const { hydrate, isDark } = usePlatformTheme()

      hydrate()

      expect(isDark.value).toBe(true)
    })
  })

  describe('toggle', () => {
    it('switches from dark to light and persists', () => {
      const { toggle, isDark } = usePlatformTheme()
      isDark.value = true

      toggle()

      expect(isDark.value).toBe(false)
      expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
    })

    it('switches from light to dark and persists', () => {
      const { toggle, isDark } = usePlatformTheme()
      isDark.value = false

      toggle()

      expect(isDark.value).toBe(true)
      expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
    })
  })
})
