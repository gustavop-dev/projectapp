/**
 * @jest-environment node
 *
 * Tests for usePlatformApi SSR branches (window undefined).
 * Uses Node.js environment where window is genuinely undefined.
 */

describe('usePlatformApi (SSR — window undefined)', () => {
  let readPlatformSession, writePlatformSession, clearPlatformSession

  beforeEach(() => {
    jest.resetModules()
    const mod = require('../../composables/usePlatformApi')
    readPlatformSession = mod.readPlatformSession
    writePlatformSession = mod.writePlatformSession
    clearPlatformSession = mod.clearPlatformSession
  })

  it('readPlatformSession returns empty session when window is undefined', () => {
    const session = readPlatformSession()

    expect(session.accessToken).toBe('')
    expect(session.refreshToken).toBe('')
    expect(session.user).toBeNull()
    expect(session.verificationToken).toBe('')
    expect(session.pendingEmail).toBe('')
  })

  it('writePlatformSession returns early when window is undefined', () => {
    expect(() => writePlatformSession({ accessToken: 'tok' })).not.toThrow()
  })

  it('clearPlatformSession returns early when window is undefined', () => {
    expect(() => clearPlatformSession()).not.toThrow()
  })
})
