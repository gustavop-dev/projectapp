import { useAdditionalModulesTheme } from '../../composables/useAdditionalModulesTheme'

const STORAGE_KEY = 'projectapp-additional-modules-theme'

describe('useAdditionalModulesTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to light mode', () => {
    const { theme, isDark } = useAdditionalModulesTheme()

    expect(theme.value).toBe('light')
    expect(isDark.value).toBe(false)
  })

  it('restores a saved dark theme', () => {
    window.localStorage.setItem(STORAGE_KEY, 'dark')

    const { theme, isDark } = useAdditionalModulesTheme()

    expect(theme.value).toBe('dark')
    expect(isDark.value).toBe(true)
  })

  it('persists a theme toggle immediately', () => {
    const { isDark, toggle } = useAdditionalModulesTheme()

    toggle()

    expect(isDark.value).toBe(true)
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('normalizes an unsupported stored theme', () => {
    window.localStorage.setItem(STORAGE_KEY, 'sepia')

    const { theme } = useAdditionalModulesTheme()

    expect(theme.value).toBe('light')
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('light')
  })
})
