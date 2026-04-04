/**
 * @jest-environment node
 *
 * Tests for usePlatformSidebar SSR guard branches (window is undefined).
 * Runs in Node.js environment where `window` is genuinely not defined.
 */

const { usePlatformSidebar } = require('../../composables/usePlatformSidebar')

describe('usePlatformSidebar (SSR — window undefined)', () => {
  it('hydrate returns early when window is undefined', () => {
    const { hydrate, isCollapsed } = usePlatformSidebar()
    isCollapsed.value = true

    hydrate()

    expect(isCollapsed.value).toBe(true)
  })

  it('toggle skips localStorage when window is undefined', () => {
    const { toggle, isCollapsed } = usePlatformSidebar()
    isCollapsed.value = false

    toggle()

    expect(isCollapsed.value).toBe(true)
  })

  it('collapse skips localStorage when window is undefined', () => {
    const { collapse, isCollapsed } = usePlatformSidebar()
    isCollapsed.value = false

    collapse()

    expect(isCollapsed.value).toBe(true)
  })

  it('expand skips localStorage when window is undefined', () => {
    const { expand, isCollapsed } = usePlatformSidebar()
    isCollapsed.value = true

    expand()

    expect(isCollapsed.value).toBe(false)
  })

  it('setupResizeListener returns early when window is undefined', () => {
    const { setupResizeListener } = usePlatformSidebar()
    expect(() => setupResizeListener()).not.toThrow()
  })

  it('cleanupResizeListener returns early when window is undefined', () => {
    const { cleanupResizeListener } = usePlatformSidebar()
    expect(() => cleanupResizeListener()).not.toThrow()
  })
})
