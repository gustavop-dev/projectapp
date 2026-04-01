/**
 * Tests for usePlatformCustomTheme composable.
 */

const mockAuthStore = {
  user: null,
  updateProfile: jest.fn().mockResolvedValue(undefined),
}

jest.mock('../../stores/platform-auth', () => ({
  usePlatformAuthStore: () => mockAuthStore,
}))

const mockRequest = jest.fn()

jest.mock('../../composables/usePlatformApi', () => ({
  usePlatformApi: () => ({ request: mockRequest }),
}))

describe('usePlatformCustomTheme', () => {
  let usePlatformCustomTheme

  beforeEach(() => {
    jest.resetModules()
    mockAuthStore.user = null
    mockAuthStore.updateProfile.mockClear().mockResolvedValue(undefined)
    mockRequest.mockReset()
    document.documentElement.removeAttribute('style')
    usePlatformCustomTheme = require('../../composables/usePlatformCustomTheme').usePlatformCustomTheme
  })

  it('hydrate copies user theme fields once', () => {
    mockAuthStore.user = {
      theme_color: '#2874f3',
      cover_image: 'x.jpg',
      custom_cover_image: '',
    }
    const theme = usePlatformCustomTheme()
    theme.hydrate()
    expect(theme.themeColor.value).toBe('#2874f3')
    expect(theme.coverImage.value).toBe('x.jpg')
  })

  it('hydrate skips re-run when already initialized', () => {
    mockAuthStore.user = { theme_color: '#2874f3', cover_image: '', custom_cover_image: '' }
    const theme = usePlatformCustomTheme()
    theme.hydrate()
    mockAuthStore.user = { theme_color: '#000000', cover_image: '', custom_cover_image: '' }
    theme.hydrate()
    expect(theme.themeColor.value).toBe('#2874f3')
  })

  it('applyTheme sets CSS variables for palette color', () => {
    const theme = usePlatformCustomTheme()
    theme.themeColor.value = '#2874f3'
    theme.applyTheme()
    expect(document.documentElement.style.getPropertyValue('--theme-color')).toBe('#2874f3')
  })

  it('applyTheme uses fallback rgba when hex not in palette', () => {
    const theme = usePlatformCustomTheme()
    theme.themeColor.value = '#aabbcc'
    theme.applyTheme()
    expect(document.documentElement.style.getPropertyValue('--theme-surface')).toContain('rgba')
  })

  it('applyTheme removes vars when color cleared', () => {
    const theme = usePlatformCustomTheme()
    theme.themeColor.value = '#2874f3'
    theme.applyTheme()
    theme.themeColor.value = ''
    theme.applyTheme()
    expect(document.documentElement.style.getPropertyValue('--theme-color')).toBe('')
  })

  it('setThemeColor updates profile', async () => {
    const theme = usePlatformCustomTheme()
    await theme.setThemeColor('#2874f3')
    expect(mockAuthStore.updateProfile).toHaveBeenCalledWith({ theme_color: '#2874f3' })
  })

  it('setCoverImage clears custom url and calls updateProfile', async () => {
    const theme = usePlatformCustomTheme()
    theme.customCoverImageUrl.value = 'https://old'
    await theme.setCoverImage('n.jpg')
    expect(theme.coverImage.value).toBe('n.jpg')
    expect(theme.customCoverImageUrl.value).toBe('')
    expect(mockAuthStore.updateProfile).toHaveBeenCalledWith({ cover_image: 'n.jpg' })
  })

  it('setCustomCoverImage updates user from response', async () => {
    mockRequest.mockResolvedValueOnce({
      data: { id: 1, custom_cover_image: 'https://cdn/x.png', cover_image: '' },
    })
    const theme = usePlatformCustomTheme()
    const file = new File(['b'], 'c.png', { type: 'image/png' })
    await theme.setCustomCoverImage(file)
    expect(mockRequest).toHaveBeenCalled()
    expect(theme.customCoverImageUrl.value).toBe('https://cdn/x.png')
    expect(mockAuthStore.user.custom_cover_image).toBe('https://cdn/x.png')
  })

  it('clearCover resets cover fields', async () => {
    const theme = usePlatformCustomTheme()
    theme.coverImage.value = 'a.jpg'
    theme.customCoverImageUrl.value = 'https://u'
    await theme.clearCover()
    expect(theme.coverImage.value).toBe('')
    expect(theme.customCoverImageUrl.value).toBe('')
    expect(theme.isCoverDark.value).toBe(false)
  })

  it('clearAll resets theme and cover', async () => {
    const theme = usePlatformCustomTheme()
    theme.themeColor.value = '#2874f3'
    theme.coverImage.value = 'x.jpg'
    await theme.clearAll()
    expect(theme.themeColor.value).toBe('')
    expect(theme.coverImage.value).toBe('')
  })

  it('computed hasTheme reflects themeColor', () => {
    const theme = usePlatformCustomTheme()
    expect(theme.hasTheme.value).toBe(false)
    theme.themeColor.value = '#2874f3'
    expect(theme.hasTheme.value).toBe(true)
  })

  it('computed hasCover reflects cover fields', () => {
    const theme = usePlatformCustomTheme()
    theme.coverImage.value = 'a.jpg'
    expect(theme.hasCover.value).toBe(true)
  })

  it('setCoverImage marks cover dark when sampled brightness is low', async () => {
    global.Image = class {
      set onload(fn) {
        this._on = fn
      }

      set onerror(_fn) {}

      set src(_v) {
        queueMicrotask(() => this._on())
      }
    }
    const origCreate = document.createElement.bind(document)
    jest.spyOn(document, 'createElement').mockImplementation((tag) => {
      if (tag === 'canvas') {
        return {
          width: 64,
          height: 64,
          getContext: () => ({
            drawImage: jest.fn(),
            getImageData: () => ({ data: new Uint8ClampedArray(64 * 64 * 4).fill(5) }),
          }),
        }
      }
      return origCreate(tag)
    })
    const theme = usePlatformCustomTheme()
    await theme.setCoverImage('dark.jpg')
    await Promise.resolve()
    await Promise.resolve()
    expect(theme.isCoverDark.value).toBe(true)
    document.createElement.mockRestore()
  })

  it('setThemeColor ignores updateProfile rejection', async () => {
    mockAuthStore.updateProfile.mockRejectedValueOnce(new Error('net'))
    const theme = usePlatformCustomTheme()
    await expect(theme.setThemeColor('#2874f3')).resolves.toBeUndefined()
  })
})
