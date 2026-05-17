/**
 * Tests for the password-reset slice of the platform-auth store.
 *
 * Covers: passwordReset initial state, startPasswordReset, markCodeVerified,
 * clearPasswordReset, and that logout() wipes the slice along with the rest.
 */
import { setActivePinia, createPinia } from 'pinia'
import { usePlatformAuthStore } from '../../stores/platform-auth'

jest.mock('../../composables/usePlatformApi', () => {
  const mockPost = jest.fn()
  return {
    usePlatformApi: () => ({
      post: mockPost,
      get: jest.fn(),
      patch: jest.fn(),
      request: jest.fn(),
      refreshPlatformAccessToken: jest.fn(),
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
  }
})

const { __mockPost: mockPost } = require('../../composables/usePlatformApi')

describe('platform-auth — password reset slice', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = usePlatformAuthStore()
    jest.clearAllMocks()
  })

  it('starts with an empty passwordReset slice', () => {
    expect(store.passwordReset).toEqual({
      email: null,
      requestToken: null,
      verifiedToken: null,
    })
  })

  it('startPasswordReset stores email + request token and clears verified', () => {
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    expect(store.passwordReset).toEqual({
      email: 'a@b.co',
      requestToken: 'req-tok',
      verifiedToken: null,
    })
  })

  it('markCodeVerified stores the verified token without losing email', () => {
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    store.markCodeVerified({ verifiedToken: 'ver-tok' })
    expect(store.passwordReset).toEqual({
      email: 'a@b.co',
      requestToken: 'req-tok',
      verifiedToken: 'ver-tok',
    })
  })

  it('clearPasswordReset wipes all three fields', () => {
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    store.markCodeVerified({ verifiedToken: 'ver-tok' })
    store.clearPasswordReset()
    expect(store.passwordReset).toEqual({
      email: null,
      requestToken: null,
      verifiedToken: null,
    })
  })

  it('logout also wipes passwordReset (via resetState)', () => {
    store.startPasswordReset({ email: 'a@b.co', requestToken: 'req-tok' })
    store.logout()
    expect(store.passwordReset).toEqual({
      email: null,
      requestToken: null,
      verifiedToken: null,
    })
  })
})
