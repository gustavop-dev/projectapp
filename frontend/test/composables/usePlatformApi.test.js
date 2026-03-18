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

    it('writes verificationToken to localStorage', () => {
      writePlatformSession({ verificationToken: 'vtoken-123' })

      expect(localStorage.getItem(STORAGE_KEYS.verificationToken)).toBe('vtoken-123')
    })

    it('removes verificationToken when null', () => {
      localStorage.setItem(STORAGE_KEYS.verificationToken, 'old')

      writePlatformSession({ verificationToken: null })

      expect(localStorage.getItem(STORAGE_KEYS.verificationToken)).toBeNull()
    })

    it('writes pendingEmail to localStorage', () => {
      writePlatformSession({ pendingEmail: 'test@example.com' })

      expect(localStorage.getItem(STORAGE_KEYS.pendingEmail)).toBe('test@example.com')
    })

    it('removes pendingEmail when empty string', () => {
      localStorage.setItem(STORAGE_KEYS.pendingEmail, 'old@test.com')

      writePlatformSession({ pendingEmail: '' })

      expect(localStorage.getItem(STORAGE_KEYS.pendingEmail)).toBeNull()
    })

    it('ignores keys with undefined value in setOrRemoveStorageValue', () => {
      localStorage.setItem(STORAGE_KEYS.accessToken, 'keep')

      writePlatformSession({ accessToken: undefined })

      expect(localStorage.getItem(STORAGE_KEYS.accessToken)).toBe('keep')
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

describe('usePlatformApi interceptors', () => {
  let requestInterceptor, responseSuccessInterceptor, responseErrorInterceptor
  let mockAxiosInstance, mockAxiosPost
  beforeEach(() => {
    localStorage.clear()
    jest.resetModules()

    requestInterceptor = null
    responseSuccessInterceptor = null
    responseErrorInterceptor = null

    mockAxiosInstance = {
      interceptors: {
        request: {
          use: jest.fn((fn) => {
            requestInterceptor = fn
          }),
        },
        response: {
          use: jest.fn((success, error) => {
            responseSuccessInterceptor = success
            responseErrorInterceptor = error
          }),
        },
      },
      request: jest.fn().mockResolvedValue({ data: {} }),
    }
    mockAxiosInstance.mockReturnSelf = mockAxiosInstance

    mockAxiosPost = jest.fn()

    jest.doMock('axios', () => ({
      __esModule: true,
      default: {
        create: jest.fn(() => mockAxiosInstance),
        post: mockAxiosPost,
      },
    }))

    const mod = require('../../composables/usePlatformApi')
    mod.usePlatformApi()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('request interceptor', () => {
    it('skips auth header when skipPlatformAuth is true', () => {
      const config = { skipPlatformAuth: true, headers: {} }

      const result = requestInterceptor(config)

      expect(result).toBe(config)
      expect(result.headers.Authorization).toBeUndefined()
    })

    it('skips auth when Authorization header already present', () => {
      localStorage.setItem('platform_access_token', 'my-token')
      const config = { headers: { Authorization: 'Bearer existing' } }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer existing')
    })

    it('skips auth when lowercase authorization header present', () => {
      localStorage.setItem('platform_access_token', 'my-token')
      const config = { headers: { authorization: 'Bearer existing' } }

      const result = requestInterceptor(config)

      expect(result.headers.authorization).toBe('Bearer existing')
    })

    it('skips auth when no access token in session', () => {
      const config = { headers: {} }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })

    it('attaches Bearer token from session', () => {
      localStorage.setItem('platform_access_token', 'acc-token')
      const config = { headers: {} }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer acc-token')
    })
  })

  describe('response interceptor', () => {
    it('passes through successful responses', () => {
      const response = { data: { ok: true } }

      const result = responseSuccessInterceptor(response)

      expect(result).toBe(response)
    })

    it('throws error for non-401 status', async () => {
      const error = {
        config: { url: 'some-url/' },
        response: { status: 500 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('throws error for 401 on login endpoint', async () => {
      const error = {
        config: { url: 'login/' },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('throws error for 401 on verify endpoint', async () => {
      const error = {
        config: { url: 'verify/' },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('throws error for 401 on resend-code endpoint', async () => {
      const error = {
        config: { url: 'resend-code/' },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('throws error for 401 on token/refresh endpoint', async () => {
      const error = {
        config: { url: 'token/refresh/' },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('throws error for 401 when _platformRetry is set', async () => {
      const error = {
        config: { url: 'some-url/', _platformRetry: true },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('throws error for 401 when skipPlatformRefresh is set', async () => {
      const error = {
        config: { url: 'some-url/', skipPlatformRefresh: true },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)
    })

    it('clears session and throws when 401 with no refresh token', async () => {
      const error = {
        config: { url: 'some-url/', headers: {} },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error)).rejects.toBe(error)

      expect(localStorage.getItem('platform_access_token')).toBeNull()
    })

    it('attempts token refresh on 401 with refresh token', async () => {
      jest.resetModules()
      localStorage.clear()
      localStorage.setItem('platform_refresh_token', 'ref-tok')
      localStorage.setItem('platform_access_token', 'old-acc')

      delete window.location
      window.location = { pathname: '/platform/dashboard', search: '', href: '' }

      requestInterceptor = null
      responseErrorInterceptor = null

      const retryResponse = { data: { retried: true } }

      const callableMock = jest.fn().mockResolvedValue(retryResponse)
      callableMock.interceptors = {
        request: { use: jest.fn((fn) => { requestInterceptor = fn }) },
        response: {
          use: jest.fn((success, errorHandler) => {
            responseSuccessInterceptor = success
            responseErrorInterceptor = errorHandler
          }),
        },
      }

      jest.doMock('axios', () => ({
        __esModule: true,
        default: {
          create: jest.fn(() => callableMock),
          post: jest.fn().mockResolvedValue({
            data: { access: 'new-acc', refresh: 'new-ref' },
          }),
        },
      }))

      const mod2 = require('../../composables/usePlatformApi')
      mod2.usePlatformApi()

      const error2 = {
        config: { url: 'some-url/', headers: {} },
        response: { status: 401 },
      }

      const result = await responseErrorInterceptor(error2)

      expect(result).toEqual(retryResponse)
      expect(localStorage.getItem('platform_access_token')).toBe('new-acc')
      expect(localStorage.getItem('platform_refresh_token')).toBe('new-ref')
    })

    it('clears session and throws when refresh fails', async () => {
      jest.resetModules()
      localStorage.clear()
      localStorage.setItem('platform_refresh_token', 'ref-tok')

      requestInterceptor = null
      responseErrorInterceptor = null

      const inst = {
        interceptors: {
          request: { use: jest.fn((fn) => { requestInterceptor = fn }) },
          response: { use: jest.fn((_s, e) => { responseErrorInterceptor = e }) },
        },
      }

      jest.doMock('axios', () => ({
        __esModule: true,
        default: {
          create: jest.fn(() => inst),
          post: jest.fn().mockRejectedValue(new Error('refresh failed')),
        },
      }))

      const mod3 = require('../../composables/usePlatformApi')
      mod3.usePlatformApi()

      const error3 = {
        config: { url: 'some-url/', headers: {} },
        response: { status: 401 },
      }

      await expect(responseErrorInterceptor(error3)).rejects.toThrow('refresh failed')

      expect(localStorage.getItem('platform_access_token')).toBeNull()
      expect(localStorage.getItem('platform_refresh_token')).toBeNull()
    })
  })

  describe('refreshPlatformAccessToken with valid refresh token', () => {
    it('refreshes token and updates session', async () => {
      jest.resetModules()
      localStorage.clear()
      localStorage.setItem('platform_refresh_token', 'ref-tok')

      jest.doMock('axios', () => ({
        __esModule: true,
        default: {
          create: jest.fn(() => ({
            interceptors: {
              request: { use: jest.fn() },
              response: { use: jest.fn() },
            },
          })),
          post: jest.fn().mockResolvedValue({
            data: { access: 'new-access', refresh: 'new-refresh' },
          }),
        },
      }))

      const mod = require('../../composables/usePlatformApi')
      const api = mod.usePlatformApi()

      const result = await api.refreshPlatformAccessToken()

      expect(result.accessToken).toBe('new-access')
      expect(result.refreshToken).toBe('new-refresh')
      expect(localStorage.getItem('platform_access_token')).toBe('new-access')
      expect(localStorage.getItem('platform_refresh_token')).toBe('new-refresh')
    })

    it('keeps original refresh token when response has no refresh field', async () => {
      jest.resetModules()
      localStorage.clear()
      localStorage.setItem('platform_refresh_token', 'original-ref')

      jest.doMock('axios', () => ({
        __esModule: true,
        default: {
          create: jest.fn(() => ({
            interceptors: {
              request: { use: jest.fn() },
              response: { use: jest.fn() },
            },
          })),
          post: jest.fn().mockResolvedValue({
            data: { access: 'new-access' },
          }),
        },
      }))

      const mod = require('../../composables/usePlatformApi')
      const api = mod.usePlatformApi()

      const result = await api.refreshPlatformAccessToken()

      expect(result.accessToken).toBe('new-access')
      expect(result.refreshToken).toBe('original-ref')
    })
  })
})
