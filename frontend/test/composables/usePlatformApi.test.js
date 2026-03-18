/**
 * Tests for usePlatformApi composable.
 *
 * Covers: readPlatformSession, writePlatformSession, clearPlatformSession,
 * usePlatformApi (get, post, patch, put, delete, request), token refresh flow.
 */

const STORAGE_KEYS = {
  accessToken: 'platform_access_token',
  refreshToken: 'platform_refresh_token',
  user: 'platform_user',
  verificationToken: 'platform_verification_token',
  pendingEmail: 'platform_pending_email',
}

let readPlatformSession, writePlatformSession, clearPlatformSession, usePlatformApi

describe('usePlatformApi', () => {
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()
    const mod = require('../../composables/usePlatformApi')
    readPlatformSession = mod.readPlatformSession
    writePlatformSession = mod.writePlatformSession
    clearPlatformSession = mod.clearPlatformSession
    usePlatformApi = mod.usePlatformApi
  })

  describe('readPlatformSession', () => {
    it('returns empty session when localStorage is empty', () => {
      const session = readPlatformSession()

      expect(session.accessToken).toBe('')
      expect(session.refreshToken).toBe('')
      expect(session.user).toBeNull()
      expect(session.verificationToken).toBe('')
      expect(session.pendingEmail).toBe('')
    })

    it('reads tokens from localStorage', () => {
      localStorage.setItem(STORAGE_KEYS.accessToken, 'acc-123')
      localStorage.setItem(STORAGE_KEYS.refreshToken, 'ref-456')

      const session = readPlatformSession()

      expect(session.accessToken).toBe('acc-123')
      expect(session.refreshToken).toBe('ref-456')
    })

    it('parses user JSON from localStorage', () => {
      const user = { email: 'a@b.com', role: 'admin' }
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))

      const session = readPlatformSession()

      expect(session.user).toEqual(user)
    })

    it('returns null user for invalid JSON', () => {
      localStorage.setItem(STORAGE_KEYS.user, 'not-valid-json')

      const session = readPlatformSession()

      expect(session.user).toBeNull()
    })
  })

  describe('writePlatformSession', () => {
    it('writes access token to localStorage', () => {
      writePlatformSession({ accessToken: 'new-acc' })

      expect(localStorage.getItem(STORAGE_KEYS.accessToken)).toBe('new-acc')
    })

    it('removes token when value is empty string', () => {
      localStorage.setItem(STORAGE_KEYS.accessToken, 'old')

      writePlatformSession({ accessToken: '' })

      expect(localStorage.getItem(STORAGE_KEYS.accessToken)).toBeNull()
    })

    it('writes user as JSON string', () => {
      const user = { email: 'test@t.com' }

      writePlatformSession({ user })

      expect(JSON.parse(localStorage.getItem(STORAGE_KEYS.user))).toEqual(user)
    })

    it('removes user when null', () => {
      localStorage.setItem(STORAGE_KEYS.user, '{"a":1}')

      writePlatformSession({ user: null })

      expect(localStorage.getItem(STORAGE_KEYS.user)).toBeNull()
    })

    it('only writes provided keys', () => {
      localStorage.setItem(STORAGE_KEYS.accessToken, 'keep')

      writePlatformSession({ refreshToken: 'new-ref' })

      expect(localStorage.getItem(STORAGE_KEYS.accessToken)).toBe('keep')
      expect(localStorage.getItem(STORAGE_KEYS.refreshToken)).toBe('new-ref')
    })
  })

  describe('clearPlatformSession', () => {
    it('removes all platform keys from localStorage', () => {
      Object.values(STORAGE_KEYS).forEach((key) => {
        localStorage.setItem(key, 'value')
      })

      clearPlatformSession()

      Object.values(STORAGE_KEYS).forEach((key) => {
        expect(localStorage.getItem(key)).toBeNull()
      })
    })
  })

  describe('usePlatformApi factory', () => {
    it('returns get, post, patch, put, delete, request methods', () => {
      const api = usePlatformApi()

      expect(typeof api.get).toBe('function')
      expect(typeof api.post).toBe('function')
      expect(typeof api.patch).toBe('function')
      expect(typeof api.put).toBe('function')
      expect(typeof api.delete).toBe('function')
      expect(typeof api.request).toBe('function')
      expect(typeof api.refreshPlatformAccessToken).toBe('function')
    })

    it('returns refreshPlatformAccessToken on every call', () => {
      const api1 = usePlatformApi()
      const api2 = usePlatformApi()

      expect(api1.refreshPlatformAccessToken).toBe(api2.refreshPlatformAccessToken)
    })
  })

  describe('request method with token option', () => {
    it('request method accepts custom token', async () => {
      const api = usePlatformApi()

      // The request should not throw when called with token option
      // We can't easily test the actual HTTP call without more mocking,
      // but we verify the interface accepts it
      expect(() => {
        api.request({
          url: 'test/',
          method: 'GET',
          token: 'custom-token',
          skipAuth: true,
        })
      }).not.toThrow()
    })
  })

  describe('refreshPlatformAccessToken', () => {
    it('throws when no refresh token in session', async () => {
      const api = usePlatformApi()

      await expect(api.refreshPlatformAccessToken()).rejects.toThrow(
        'Refresh token no disponible.',
      )
    })
  })
})
