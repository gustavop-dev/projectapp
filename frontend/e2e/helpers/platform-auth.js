/**
 * Platform auth helpers for E2E tests.
 *
 * Sets JWT session data in localStorage so platform pages
 * render as if the user is already authenticated.
 */

export const PLATFORM_STORAGE_KEYS = {
  accessToken: 'platform_access_token',
  refreshToken: 'platform_refresh_token',
  user: 'platform_user',
  verificationToken: 'platform_verification_token',
  pendingEmail: 'platform_pending_email',
}

export const mockPlatformAdmin = {
  id: 9001,
  user_id: 9001,
  email: 'admin@e2e-test.com',
  first_name: 'Admin',
  last_name: 'E2E',
  role: 'admin',
  company_name: 'ProjectApp',
  phone: '+57 300 000 0001',
  is_onboarded: true,
  profile_completed: true,
  is_active: true,
  avatar: null,
  cedula: '1020304050',
  date_of_birth: '1990-01-15',
  gender: 'male',
  education_level: 'universitario',
}

export const mockPlatformClient = {
  id: 9002,
  user_id: 9002,
  email: 'client@e2e-test.com',
  first_name: 'Client',
  last_name: 'E2E',
  role: 'client',
  company_name: 'ACME Corp',
  phone: '+57 300 000 0002',
  is_onboarded: true,
  profile_completed: true,
  is_active: true,
  avatar: null,
  cedula: '9876543210',
  date_of_birth: '1995-06-20',
  gender: 'female',
  education_level: 'posgrado',
}

export const mockPlatformClientIncompleteProfile = {
  ...mockPlatformClient,
  id: 9003,
  user_id: 9003,
  email: 'incomplete@e2e-test.com',
  first_name: '',
  last_name: '',
  company_name: '',
  phone: '',
  profile_completed: false,
  cedula: '',
  date_of_birth: null,
  gender: '',
  education_level: '',
}

/**
 * Inject platform JWT session into localStorage before page load.
 *
 * @param {import('@playwright/test').Page} page
 * @param {{ user: object, accessToken?: string, refreshToken?: string }} options
 */
export async function setPlatformAuth(page, { user, accessToken, refreshToken } = {}) {
  const token = accessToken || 'e2e-platform-access-token'
  const refresh = refreshToken || 'e2e-platform-refresh-token'
  const userData = user || mockPlatformAdmin

  await page.addInitScript(
    ({ keys, token: t, refresh: r, user: u }) => {
      localStorage.setItem(keys.accessToken, t)
      localStorage.setItem(keys.refreshToken, r)
      localStorage.setItem(keys.user, JSON.stringify(u))
      localStorage.removeItem(keys.verificationToken)
      localStorage.removeItem(keys.pendingEmail)
    },
    { keys: PLATFORM_STORAGE_KEYS, token, refresh, user: userData },
  )
}

/**
 * Inject platform verification session (pre-onboarding).
 *
 * @param {import('@playwright/test').Page} page
 * @param {{ verificationToken?: string, email?: string }} options
 */
export async function setPlatformVerificationState(page, { verificationToken, email } = {}) {
  const vToken = verificationToken || 'e2e-verification-token'
  const pendingEmail = email || 'newuser@e2e-test.com'

  await page.addInitScript(
    ({ keys, vToken: vt, email: em }) => {
      localStorage.removeItem(keys.accessToken)
      localStorage.removeItem(keys.refreshToken)
      localStorage.removeItem(keys.user)
      localStorage.setItem(keys.verificationToken, vt)
      localStorage.setItem(keys.pendingEmail, em)
    },
    { keys: PLATFORM_STORAGE_KEYS, vToken, email: pendingEmail },
  )
}
