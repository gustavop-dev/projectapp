/**
 * Tests for usePlatformSidebar composable.
 *
 * Covers: hydrate, toggle, collapse, expand, openMobile, closeMobile,
 * toggleMobile, setupResizeListener, cleanupResizeListener.
 */

const STORAGE_KEY = 'platform_sidebar_collapsed'

let usePlatformSidebar

const ORIGINAL_INNER_WIDTH = window.innerWidth

describe('usePlatformSidebar', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()
    const mod = require('../../composables/usePlatformSidebar')
    usePlatformSidebar = mod.usePlatformSidebar
  })

  afterEach(() => {
    const { cleanupResizeListener } = usePlatformSidebar()
    cleanupResizeListener()
    Object.defineProperty(window, 'innerWidth', { value: ORIGINAL_INNER_WIDTH, writable: true })
  })

  describe('hydrate', () => {
    it('reads collapsed state from localStorage when true', () => {
      localStorage.setItem(STORAGE_KEY, 'true')
      const { hydrate, isCollapsed } = usePlatformSidebar()

      hydrate()

      expect(isCollapsed.value).toBe(true)
    })

    it('reads collapsed state from localStorage when false', () => {
      localStorage.setItem(STORAGE_KEY, 'false')
      const { hydrate, isCollapsed } = usePlatformSidebar()

      hydrate()

      expect(isCollapsed.value).toBe(false)
    })

    it('defaults based on window width when no stored value', () => {
      const { hydrate, isCollapsed } = usePlatformSidebar()

      hydrate()

      expect(typeof isCollapsed.value).toBe('boolean')
    })

    it('defaults to collapsed when no stored value and width below 1024', () => {
      Object.defineProperty(window, 'innerWidth', { value: 800, writable: true })
      const { hydrate, isCollapsed } = usePlatformSidebar()
      isCollapsed.value = false

      hydrate()

      expect(isCollapsed.value).toBe(true)
    })

    it('defaults to expanded when no stored value and width at 1024 or above', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1440, writable: true })
      const { hydrate, isCollapsed } = usePlatformSidebar()
      isCollapsed.value = true

      hydrate()

      expect(isCollapsed.value).toBe(false)
    })
  })

  describe('toggle', () => {
    it('flips collapsed state and persists to localStorage', () => {
      const { toggle, isCollapsed } = usePlatformSidebar()
      isCollapsed.value = false

      toggle()

      expect(isCollapsed.value).toBe(true)
      expect(localStorage.getItem(STORAGE_KEY)).toBe('true')
    })

    it('toggles back from collapsed to expanded', () => {
      const { toggle, isCollapsed } = usePlatformSidebar()
      isCollapsed.value = true

      toggle()

      expect(isCollapsed.value).toBe(false)
      expect(localStorage.getItem(STORAGE_KEY)).toBe('false')
    })
  })

  describe('collapse', () => {
    it('sets collapsed to true and persists', () => {
      const { collapse, isCollapsed } = usePlatformSidebar()
      isCollapsed.value = false

      collapse()

      expect(isCollapsed.value).toBe(true)
      expect(localStorage.getItem(STORAGE_KEY)).toBe('true')
    })
  })

  describe('expand', () => {
    it('sets collapsed to false and persists', () => {
      const { expand, isCollapsed } = usePlatformSidebar()
      isCollapsed.value = true

      expand()

      expect(isCollapsed.value).toBe(false)
      expect(localStorage.getItem(STORAGE_KEY)).toBe('false')
    })
  })

  describe('mobile controls', () => {
    it('openMobile sets isMobileOpen to true', () => {
      const { openMobile, isMobileOpen } = usePlatformSidebar()
      isMobileOpen.value = false

      openMobile()

      expect(isMobileOpen.value).toBe(true)
    })

    it('closeMobile sets isMobileOpen to false', () => {
      const { closeMobile, isMobileOpen } = usePlatformSidebar()
      isMobileOpen.value = true

      closeMobile()

      expect(isMobileOpen.value).toBe(false)
    })

    it('toggleMobile flips isMobileOpen', () => {
      const { toggleMobile, isMobileOpen } = usePlatformSidebar()
      isMobileOpen.value = false

      toggleMobile()

      expect(isMobileOpen.value).toBe(true)

      toggleMobile()

      expect(isMobileOpen.value).toBe(false)
    })
  })

  describe('resize listener', () => {
    it('setupResizeListener adds event listener', () => {
      const addSpy = jest.spyOn(window, 'addEventListener')
      const { setupResizeListener } = usePlatformSidebar()

      setupResizeListener()

      expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function))
      addSpy.mockRestore()
    })

    it('cleanupResizeListener removes event listener', () => {
      const removeSpy = jest.spyOn(window, 'removeEventListener')
      const { cleanupResizeListener } = usePlatformSidebar()

      cleanupResizeListener()

      expect(removeSpy).toHaveBeenCalledWith('resize', expect.any(Function))
      removeSpy.mockRestore()
    })

    it('closes mobile menu when window width drops below breakpoint', () => {
      const { setupResizeListener, openMobile, isMobileOpen, cleanupResizeListener: cleanup } = usePlatformSidebar()
      openMobile()
      expect(isMobileOpen.value).toBe(true)

      setupResizeListener()

      Object.defineProperty(window, 'innerWidth', { value: 500, writable: true })
      window.dispatchEvent(new Event('resize'))

      expect(isMobileOpen.value).toBe(false)

      Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true })
      cleanup()
    })

    it('keeps mobile menu open when window width is above breakpoint', () => {
      const { setupResizeListener, openMobile, isMobileOpen, cleanupResizeListener: cleanup } = usePlatformSidebar()
      openMobile()

      setupResizeListener()

      Object.defineProperty(window, 'innerWidth', { value: 900, writable: true })
      window.dispatchEvent(new Event('resize'))

      expect(isMobileOpen.value).toBe(true)

      Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true })
      cleanup()
    })
  })
})
