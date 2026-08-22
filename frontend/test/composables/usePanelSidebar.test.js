/**
 * Tests for usePanelSidebar composable.
 */
const STORAGE_KEY = 'panel_sidebar_collapsed'

let usePanelSidebar

const ORIGINAL_INNER_WIDTH = window.innerWidth

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
    window.innerWidth = ORIGINAL_INNER_WIDTH
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

  it('handleResize keeps the drawer open inside the mobile navigation range', () => {
    const { setupResizeListener, openMobile, isMobileOpen } = usePanelSidebar()
    openMobile()
    window.innerWidth = 500
    setupResizeListener()
    window.dispatchEvent(new Event('resize'))
    expect(isMobileOpen.value).toBe(true)
  })

  it('handleResize closes the drawer when desktop navigation becomes available', () => {
    const { setupResizeListener, openMobile, isMobileOpen } = usePanelSidebar()
    openMobile()
    window.innerWidth = 1024
    setupResizeListener()
    window.dispatchEvent(new Event('resize'))
    expect(isMobileOpen.value).toBe(false)
  })

  it.each([835, 1195, 1279])('hydrate defaults to collapsed at %ipx', (width) => {
    window.innerWidth = width
    const { hydrate, isCollapsed } = usePanelSidebar()
    isCollapsed.value = false
    hydrate()
    expect(isCollapsed.value).toBe(true)
  })

  it('hydrate defaults to expanded at the desktop breakpoint', () => {
    window.innerWidth = 1440
    const { hydrate, isCollapsed } = usePanelSidebar()
    isCollapsed.value = true
    hydrate()
    expect(isCollapsed.value).toBe(false)
  })

  it('toggle from collapsed expands and persists false', () => {
    const { toggle, isCollapsed } = usePanelSidebar()
    isCollapsed.value = true
    toggle()
    expect(isCollapsed.value).toBe(false)
    expect(localStorage.getItem(STORAGE_KEY)).toBe('false')
  })

  it('collapse persists true to localStorage', () => {
    const { collapse } = usePanelSidebar()
    collapse()
    expect(localStorage.getItem(STORAGE_KEY)).toBe('true')
  })

  it('expand persists false to localStorage', () => {
    const { expand } = usePanelSidebar()
    expand()
    expect(localStorage.getItem(STORAGE_KEY)).toBe('false')
  })

  it('cleanupResizeListener removes the resize handler', () => {
    const { setupResizeListener, cleanupResizeListener, openMobile, isMobileOpen } = usePanelSidebar()
    setupResizeListener()
    cleanupResizeListener()
    openMobile()
    window.innerWidth = 400
    window.dispatchEvent(new Event('resize'))
    expect(isMobileOpen.value).toBe(true)
  })
})
