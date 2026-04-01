/**
 * Tests for usePanelSidebar composable.
 */
const STORAGE_KEY = 'panel_sidebar_collapsed'

let usePanelSidebar

describe('usePanelSidebar', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()
    const mod = require('../../composables/usePanelSidebar')
    usePanelSidebar = mod.usePanelSidebar
  })

  afterEach(() => {
    const { cleanupResizeListener } = usePanelSidebar()
    cleanupResizeListener()
  })

  it('hydrate reads true from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    const { hydrate, isCollapsed } = usePanelSidebar()
    hydrate()
    expect(isCollapsed.value).toBe(true)
  })

  it('hydrate reads false from localStorage', () => {
    localStorage.setItem(STORAGE_KEY, 'false')
    const { hydrate, isCollapsed } = usePanelSidebar()
    hydrate()
    expect(isCollapsed.value).toBe(false)
  })

  it('toggle flips collapsed and persists', () => {
    const { toggle, isCollapsed } = usePanelSidebar()
    isCollapsed.value = false
    toggle()
    expect(isCollapsed.value).toBe(true)
    expect(localStorage.getItem(STORAGE_KEY)).toBe('true')
  })

  it('collapse sets true and persists', () => {
    const { collapse, isCollapsed } = usePanelSidebar()
    isCollapsed.value = false
    collapse()
    expect(isCollapsed.value).toBe(true)
  })

  it('expand sets false and persists', () => {
    const { expand, isCollapsed } = usePanelSidebar()
    isCollapsed.value = true
    expand()
    expect(isCollapsed.value).toBe(false)
  })

  it('openMobile sets isMobileOpen true', () => {
    const { openMobile, isMobileOpen } = usePanelSidebar()
    openMobile()
    expect(isMobileOpen.value).toBe(true)
  })

  it('closeMobile sets isMobileOpen false', () => {
    const { openMobile, closeMobile, isMobileOpen } = usePanelSidebar()
    openMobile()
    closeMobile()
    expect(isMobileOpen.value).toBe(false)
  })

  it('toggleMobile flips isMobileOpen', () => {
    const { toggleMobile, isMobileOpen } = usePanelSidebar()
    toggleMobile()
    expect(isMobileOpen.value).toBe(true)
    toggleMobile()
    expect(isMobileOpen.value).toBe(false)
  })

  it('handleResize closes mobile when width below breakpoint', () => {
    const { setupResizeListener, openMobile, isMobileOpen } = usePanelSidebar()
    openMobile()
    window.innerWidth = 500
    setupResizeListener()
    window.dispatchEvent(new Event('resize'))
    expect(isMobileOpen.value).toBe(false)
  })

})
