import { useFinancingTheme } from '../../composables/useFinancingTheme'


describe('useFinancingTheme', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to light mode', () => {
    const { theme, isDark } = useFinancingTheme()

    expect(theme.value).toBe('light')
    expect(isDark.value).toBe(false)
  })

  it('persists a dark theme selection', () => {
    const { isDark, toggle } = useFinancingTheme()

    toggle()

    expect(isDark.value).toBe(true)
    expect(window.localStorage.getItem('projectapp-financing-theme')).toBe('dark')
  })

  it('normalizes an unsupported saved theme', () => {
    window.localStorage.setItem('projectapp-financing-theme', 'sepia')

    const { theme } = useFinancingTheme()

    expect(theme.value).toBe('light')
  })
})
