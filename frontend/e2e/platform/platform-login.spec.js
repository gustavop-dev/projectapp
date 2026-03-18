/**
 * E2E tests for platform login flow.
 *
 * @flow:platform-login
 * Covers: login page render, form validation, successful login redirect,
 *         error states, redirect to verify for unverified users,
 *         redirect to complete-profile for incomplete profiles,
 *         authenticated user redirect to dashboard.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_LOGIN } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
  mockPlatformClientIncompleteProfile,
} from '../helpers/platform-auth.js';

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

/** Default mock that handles guest page-load calls. */
function setupGuestMocks(page) {
  return mockApi(page, async () => null);
}

// quality: allow-fragile-selector (stable HTML id attribute on login form)
const emailField = (page) => page.locator('#platform-email');
// quality: allow-fragile-selector (stable HTML id attribute on login form)
const passwordField = (page) => page.locator('#platform-password');

/**
 * Wait for Nuxt hydration + GSAP entrance animation to complete.
 * GSAP usePageEntrance: 50ms delay + 0.6s duration + 0.08s stagger per element.
 * quality: allow-fragile-selector (waitForTimeout needed for Nuxt hydration + GSAP entrance animation)
 */
const loginFormReady = async (page) => {
  await page.waitForLoadState('load');
  await page.locator('#platform-email').waitFor({ state: 'visible', timeout: 15000 });
  // Allow GSAP entrance animation to fully settle (50ms delay + 0.6s + stagger)
  await page.waitForTimeout(2000);
  await expect(page.locator('#platform-email')).toBeEditable({ timeout: 5000 });
};

test.describe('Platform Login', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('renders login page with email and password fields', {
    tag: [...PLATFORM_LOGIN, '@role:guest'],
  }, async ({ page }) => {
    await setupGuestMocks(page);
    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await expect(emailField(page)).toBeVisible();
    await expect(passwordField(page)).toBeVisible();
    await expect(page.getByRole('button', { name: /iniciar sesión/i })).toBeVisible();
  });

  test('submit button is disabled when fields are empty', {
    tag: [...PLATFORM_LOGIN, '@role:guest'],
  }, async ({ page }) => {
    await setupGuestMocks(page);
    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    const submitBtn = page.getByRole('button', { name: /iniciar sesión/i });
    await expect(submitBtn).toBeDisabled();
  });

  test('shows validation error for invalid email format', {
    tag: [...PLATFORM_LOGIN, '@role:guest'],
  }, async ({ page }) => {
    await setupGuestMocks(page);
    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await emailField(page).fill('not-an-email');
    await passwordField(page).fill('somepassword');
    // Bypass HTML5 type="email" validation so the custom validator runs
    await page.evaluate(() => document.querySelector('form').setAttribute('novalidate', ''));
    await page.getByRole('button', { name: /iniciar sesión/i }).click();

    await expect(page.getByText('Ingresa un email válido.')).toBeVisible();
  });

  test('shows error message on invalid credentials', {
    tag: [...PLATFORM_LOGIN, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/login/' && method === 'POST') {
        return {
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Credenciales incorrectas.' }),
        };
      }
      return null;
    });

    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await emailField(page).fill('wrong@test.com');
    await passwordField(page).fill('wrongpass');
    await page.getByRole('button', { name: /iniciar sesión/i }).click();

    await expect(page.getByText('Credenciales incorrectas.')).toBeVisible();
  });

  test('successful login redirects onboarded user to dashboard', {
    tag: [...PLATFORM_LOGIN, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/login/' && method === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            requires_verification: false,
            tokens: { access: 'mock-access', refresh: 'mock-refresh' },
            user: mockPlatformAdmin,
          }),
        };
      }
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformAdmin);
      }
      if (apiPath.startsWith('accounts/clients')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await emailField(page).fill('admin@e2e-test.com');
    await passwordField(page).fill('validpassword');
    await page.getByRole('button', { name: /iniciar sesión/i }).click();

    await page.waitForURL('**/platform/dashboard', { timeout: 15000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });

  test('login of non-onboarded user redirects to verify page', {
    tag: [...PLATFORM_LOGIN, '@role:platform-client'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/login/' && method === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            requires_verification: true,
            verification_token: 'mock-verification-token',
            email: 'newclient@test.com',
          }),
        };
      }
      return null;
    });

    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await emailField(page).fill('newclient@test.com');
    await passwordField(page).fill('temppassword');
    await page.getByRole('button', { name: /iniciar sesión/i }).click();

    await page.waitForURL('**/platform/verify', { timeout: 15000 });
    await expect(page).toHaveURL(/\/platform\/verify/);
  });

  test('login of user with incomplete profile redirects to complete-profile', {
    tag: [...PLATFORM_LOGIN, '@role:platform-client'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/login/' && method === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            requires_verification: false,
            tokens: { access: 'mock-access', refresh: 'mock-refresh' },
            user: mockPlatformClientIncompleteProfile,
          }),
        };
      }
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformClientIncompleteProfile);
      }
      return null;
    });

    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await emailField(page).fill('incomplete@e2e-test.com');
    await passwordField(page).fill('validpassword');
    await page.getByRole('button', { name: /iniciar sesión/i }).click();

    await page.waitForURL('**/platform/complete-profile', { timeout: 15000 });
    await expect(page).toHaveURL(/\/platform\/complete-profile/);
  });

  test('already authenticated admin visiting login is redirected to dashboard', {
    tag: [...PLATFORM_LOGIN, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformAdmin);
      }
      if (apiPath.startsWith('accounts/clients')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/dashboard', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });

  test('shows deactivated account error message', {
    tag: [...PLATFORM_LOGIN, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/login/' && method === 'POST') {
        return {
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Tu cuenta ha sido desactivada. Contacta al administrador.' }),
        };
      }
      return null;
    });

    await page.goto('/platform/login', { waitUntil: 'domcontentloaded' });
    await loginFormReady(page);

    await emailField(page).fill('deactivated@test.com');
    await passwordField(page).fill('somepass');
    await page.getByRole('button', { name: /iniciar sesión/i }).click();

    await expect(page.getByText(/cuenta ha sido desactivada/)).toBeVisible();
  });
});
