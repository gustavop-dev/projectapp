import { setActivePinia, createPinia } from 'pinia'
import { usePlatformAuthStore } from '../../stores/platform-auth'

jest.mock('../../composables/usePlatformApi', () => {
  const mockPost = jest.fn()
  const mockGet = jest.fn()
  const mockPatch = jest.fn()
  const mockRequest = jest.fn()
  const mockRefresh = jest.fn()
  return {
    usePlatformApi: () => ({
      post: mockPost,
      get: mockGet,
      patch: mockPatch,
      request: mockRequest,
      refreshPlatformAccessToken: mockRefresh,
    }),
    readPlatformSession: jest.fn(() => ({
      accessToken: '',
      refreshToken: '',
      user: null,
      verificationToken: '',
      pendingEmail: '',
    })),
    writePlatformSession: jest.fn(),
    clearPlatformSession: jest.fn(),
    __mockPost: mockPost,
    __mockGet: mockGet,
    __mockPatch: mockPatch,
    __mockRequest: mockRequest,
    __mockRefresh: mockRefresh,
  }
})

const {
  readPlatformSession,
  writePlatformSession,
  clearPlatformSession,
  __mockPost: mockPost,
  __mockGet: mockGet,
  __mockPatch: mockPatch,
  __mockRequest: mockRequest,
  __mockRefresh: mockRefresh,
} = require('../../composables/usePlatformApi')

describe('usePlatformAuthStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformAuthStore()
    jest.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts unauthenticated with empty tokens', () => {
      expect(store.isAuthenticated).toBe(false)
      expect(store.accessToken).toBe('')
      expect(store.refreshToken).toBe('')
      expect(store.user).toBeNull()
      expect(store.role).toBe('')
    })

    it('starts with loading flags as false', () => {
      expect(store.isLoading).toBe(false)
      expect(store.isVerifying).toBe(false)
    })
  })

  describe('getters', () => {
    it('isAdmin returns true when role is admin', () => {
      store.role = 'admin'

      expect(store.isAdmin).toBe(true)
      expect(store.isClient).toBe(false)
    })

    it('isClient returns true when role is client', () => {
      store.role = 'client'

      expect(store.isClient).toBe(true)
      expect(store.isAdmin).toBe(false)
    })

    it('displayName returns user full name', () => {
      store.user = { first_name: 'Juan', last_name: 'Pérez', email: 'j@t.com' }

      expect(store.displayName).toBe('Juan Pérez')
    })

    it('displayName falls back to email when no name', () => {
      store.user = { first_name: '', last_name: '', email: 'j@t.com' }

      expect(store.displayName).toBe('j@t.com')
    })

    it('displayName returns ProjectApp when no user', () => {
      store.user = null

      expect(store.displayName).toBe('ProjectApp')
    })

    it('userInitials returns first letters of name', () => {
      store.user = { first_name: 'Juan', last_name: 'Pérez', email: 'j@t.com' }

      expect(store.userInitials).toBe('JP')
    })

    it('userInitials returns PA when no user', () => {
      store.user = null

      expect(store.userInitials).toBe('PA')
    })

    it('hasVerificationToken returns true when token exists', () => {
      store.verificationToken = 'some-token'

      expect(store.hasVerificationToken).toBe(true)
    })

    it('needsProfileCompletion returns true when onboarded but not completed', () => {
      store.isOnboarded = true
      store.profileCompleted = false

      expect(store.needsProfileCompletion).toBe(true)
    })

    it('needsProfileCompletion returns false when profile is completed', () => {
      store.isOnboarded = true
      store.profileCompleted = true

      expect(store.needsProfileCompletion).toBe(false)
    })
  })

  describe('login', () => {
    it('returns error when email or password is empty', async () => {
      const result = await store.login({ email: '', password: '' })

      expect(result.success).toBe(false)
      expect(store.error).toBeTruthy()
      expect(mockPost).not.toHaveBeenCalled()
    })

    it('sets authenticated session on successful login without verification', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          requires_verification: false,
          tokens: { access: 'acc', refresh: 'ref' },
          user: { role: 'admin', is_onboarded: true, profile_completed: true },
        },
      })

      const result = await store.login({ email: 'a@b.com', password: 'pass' })

      expect(result.success).toBe(true)
      expect(result.requiresVerification).toBe(false)
      expect(store.isAuthenticated).toBe(true)
      expect(store.accessToken).toBe('acc')
      expect(store.role).toBe('admin')
    })

    it('sets verification state when verification is required', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          requires_verification: true,
          verification_token: 'v-token',
          email: 'c@d.com',
        },
      })

      const result = await store.login({ email: 'c@d.com', password: 'temp' })

      expect(result.success).toBe(true)
      expect(result.requiresVerification).toBe(true)
      expect(store.verificationToken).toBe('v-token')
      expect(store.isAuthenticated).toBe(false)
    })

    it('sets error on API failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Credenciales incorrectas.' } },
      })

      const result = await store.login({ email: 'a@b.com', password: 'wrong' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Credenciales incorrectas.')
    })

    it('resets isLoading after completion', async () => {
      mockPost.mockResolvedValueOnce({
        data: { requires_verification: false, tokens: { access: 'a', refresh: 'r' }, user: {} },
      })

      await store.login({ email: 'a@b.com', password: 'p' })

      expect(store.isLoading).toBe(false)
    })
  })

  describe('verify', () => {
    beforeEach(() => {
      store.verificationToken = 'v-token'
    })

    it('returns error when no verification token', async () => {
      store.verificationToken = ''

      const result = await store.verify({ code: '123456', newPassword: 'Pass1234' })

      expect(result.success).toBe(false)
      expect(mockPost).not.toHaveBeenCalled()
    })

    it('returns error for invalid code format', async () => {
      const result = await store.verify({ code: '123', newPassword: 'Pass1234' })

      expect(result.success).toBe(false)
      expect(store.error).toContain('6 dígitos')
    })

    it('returns error for short password', async () => {
      const result = await store.verify({ code: '123456', newPassword: 'short' })

      expect(result.success).toBe(false)
      expect(store.error).toContain('8 caracteres')
    })

    it('sets authenticated session on successful verification', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          tokens: { access: 'new-acc', refresh: 'new-ref' },
          user: { role: 'client', is_onboarded: true, profile_completed: false },
        },
      })

      const result = await store.verify({ code: '123456', newPassword: 'NewPass1!' })

      expect(result.success).toBe(true)
      expect(store.isAuthenticated).toBe(true)
      expect(store.accessToken).toBe('new-acc')
    })

    it('sets error on verification failure', async () => {
      mockPost.mockRejectedValueOnce({
        response: { data: { detail: 'Código incorrecto.' } },
      })

      const result = await store.verify({ code: '999999', newPassword: 'Pass1234' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Código incorrecto.')
    })
  })

  describe('resendCode', () => {
    it('returns error when no verification token', async () => {
      store.verificationToken = ''

      const result = await store.resendCode()

      expect(result.success).toBe(false)
    })

    it('sends resend request on success', async () => {
      store.verificationToken = 'v-token'
      mockPost.mockResolvedValueOnce({
        data: { detail: 'Código reenviado.' },
      })

      const result = await store.resendCode()

      expect(result.success).toBe(true)
      expect(mockPost).toHaveBeenCalledWith(
        'resend-code/',
        {},
        expect.objectContaining({ token: 'v-token' }),
      )
    })
  })

  describe('fetchMe', () => {
    it('returns error when no access token', async () => {
      store.accessToken = ''

      const result = await store.fetchMe()

      expect(result.success).toBe(false)
    })

    it('populates user data on success', async () => {
      store.accessToken = 'tok'
      mockGet.mockResolvedValueOnce({
        data: { role: 'client', is_onboarded: true, profile_completed: true, email: 'c@d.com' },
      })

      const result = await store.fetchMe()

      expect(result.success).toBe(true)
      expect(store.role).toBe('client')
      expect(store.isOnboarded).toBe(true)
      expect(store.profileCompleted).toBe(true)
      expect(store.hasValidatedSession).toBe(true)
    })

    it('clears session on fetch failure', async () => {
      store.accessToken = 'tok'
      mockGet.mockRejectedValueOnce({
        response: { status: 401, data: { detail: 'Token inválido.' } },
      })

      const result = await store.fetchMe()

      expect(result.success).toBe(false)
      expect(store.isAuthenticated).toBe(false)
      expect(store.accessToken).toBe('')
    })
  })

  describe('updateProfile', () => {
    it('updates user data on success', async () => {
      mockPatch.mockResolvedValueOnce({
        data: { role: 'client', is_onboarded: true, profile_completed: true, first_name: 'Updated' },
      })

      const result = await store.updateProfile({ first_name: 'Updated' })

      expect(result.success).toBe(true)
      expect(store.user.first_name).toBe('Updated')
    })

    it('sets error on failure', async () => {
      mockPatch.mockRejectedValueOnce({
        response: { data: { detail: 'Error al actualizar.' } },
      })

      const result = await store.updateProfile({ first_name: 'X' })

      expect(result.success).toBe(false)
      expect(store.error).toBe('Error al actualizar.')
    })
  })

  describe('completeProfile', () => {
    it('updates profile data on success', async () => {
      mockRequest.mockResolvedValueOnce({
        data: { role: 'client', is_onboarded: true, profile_completed: true },
      })

      const result = await store.completeProfile(new FormData())

      expect(result.success).toBe(true)
      expect(store.profileCompleted).toBe(true)
    })
  })

  describe('logout', () => {
    it('clears all state and session', () => {
      store.accessToken = 'tok'
      store.isAuthenticated = true
      store.user = { email: 'a@b.com' }

      store.logout()

      expect(store.isAuthenticated).toBe(false)
      expect(store.accessToken).toBe('')
      expect(store.user).toBeNull()
      expect(clearPlatformSession).toHaveBeenCalled()
    })
  })

  describe('hydrate', () => {
    it('restores state from localStorage session', () => {
      readPlatformSession.mockReturnValueOnce({
        accessToken: 'stored-acc',
        refreshToken: 'stored-ref',
        user: { role: 'admin', is_onboarded: true, profile_completed: true },
        verificationToken: '',
        pendingEmail: '',
      })

      store.hydrate()

      expect(store.accessToken).toBe('stored-acc')
      expect(store.isAuthenticated).toBe(true)
      expect(store.role).toBe('admin')
      expect(store.hasHydrated).toBe(true)
    })

    it('does not hydrate twice', () => {
      readPlatformSession.mockReturnValueOnce({
        accessToken: 'tok', refreshToken: 'ref', user: null,
        verificationToken: '', pendingEmail: '',
      })

      store.hydrate()
      store.hydrate()

      expect(readPlatformSession).toHaveBeenCalledTimes(1)
    })

    it('handles null user gracefully', () => {
      readPlatformSession.mockReturnValueOnce({
        accessToken: '', refreshToken: '', user: null,
        verificationToken: '', pendingEmail: '',
      })

      store.hydrate()

      expect(store.isAuthenticated).toBe(false)
      expect(store.role).toBe('')
    })
  })

  describe('refreshTokenAction', () => {
    it('returns error when no refresh token', async () => {
      store.refreshToken = ''

      const result = await store.refreshTokenAction()

      expect(result.success).toBe(false)
    })

    it('updates tokens on successful refresh', async () => {
      store.refreshToken = 'old-ref'
      mockRefresh.mockResolvedValueOnce({
        accessToken: 'new-acc',
        refreshToken: 'new-ref',
      })

      const result = await store.refreshTokenAction()

      expect(result.success).toBe(true)
      expect(store.accessToken).toBe('new-acc')
      expect(store.refreshToken).toBe('new-ref')
    })

    it('logs out on refresh failure', async () => {
      store.refreshToken = 'old-ref'
      store.isAuthenticated = true
      mockRefresh.mockRejectedValueOnce(new Error('expired'))

      const result = await store.refreshTokenAction()

      expect(result.success).toBe(false)
      expect(store.isAuthenticated).toBe(false)
    })
  })
})
