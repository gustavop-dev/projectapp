/**
 * Tests for the usePlatformIncludeArchived composable.
 *
 * Covers: default value initialization via useState factory.
 */

describe('usePlatformIncludeArchived', () => {
  let usePlatformIncludeArchived

  beforeEach(() => {
    jest.resetModules()
    const { ref } = jest.requireActual('vue')
    global.useState = jest.fn((_key, factory) => ref(factory()))
    usePlatformIncludeArchived = require('../../composables/usePlatformIncludeArchived').usePlatformIncludeArchived
  })

  afterEach(() => {
    delete global.useState
  })

  it('returns a ref with default value false', () => {
    const state = usePlatformIncludeArchived()

    expect(state.value).toBe(false)
  })

  it('calls useState with the platform-admin-include-archived key', () => {
    usePlatformIncludeArchived()

    expect(global.useState).toHaveBeenCalledWith(
      'platform-admin-include-archived',
      expect.any(Function),
    )
  })
})
