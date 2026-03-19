/**
 * E2E tests for platform verify & onboarding flow.
 *
 * @flow:platform-verify-onboarding
 * Covers: verify page render, 6-digit OTP input, password fields,
 *         successful verification redirect, error states,
 *         resend code, redirect to complete-profile for incomplete profiles.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_VERIFY_ONBOARDING } from '../helpers/flow-tags.js';
import {
  setPlatformVerificationState,
  mockPlatformClient,
  mockPlatformClientIncompleteProfile,
} from '../helpers/platform-auth.js';

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

test.describe('Platform Verify & Onboarding', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformVerificationState(page, {
      verificationToken: 'e2e-verify-token',
      email: 'newuser@e2e-test.com',
    });
  });

  test('renders verification form with code inputs and password fields', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });
    await page.getByText('Confirma tu identidad').waitFor({ state: 'visible', timeout: 30000 });
    await expect(page.getByText(/código de 6 dígitos/)).toBeVisible();
    await expect(page.getByLabel('Nueva contraseña')).toBeVisible();
    await expect(page.getByLabel('Confirmar contraseña')).toBeVisible();
    await expect(page.getByRole('button', { name: /completar verificación/i })).toBeVisible();
  });

  test('shows error when code is incomplete', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    await page.getByLabel('Nueva contraseña').fill('newpassword123');
    await page.getByLabel('Confirmar contraseña').fill('newpassword123');
    await page.getByRole('button', { name: /completar verificación/i }).click();

    await expect(page.getByText(/código completo de 6 dígitos/)).toBeVisible();
  });

  test('shows error when password is too short', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    const codeInputs = page.locator('input[inputmode="numeric"]');
    for (let i = 0; i < 6; i++) {
      await codeInputs.nth(i).fill(String(i + 1));
    }

    await page.getByLabel('Nueva contraseña').fill('short');
    await page.getByLabel('Confirmar contraseña').fill('short');
    await page.getByRole('button', { name: /completar verificación/i }).click();

    await expect(page.getByText(/al menos 8 caracteres/)).toBeVisible();
  });

  test('shows error when passwords do not match', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    const codeInputs = page.locator('input[inputmode="numeric"]');
    for (let i = 0; i < 6; i++) {
      await codeInputs.nth(i).fill(String(i + 1));
    }

    await page.getByLabel('Nueva contraseña').fill('newpassword123');
    await page.getByLabel('Confirmar contraseña').fill('differentpassword');
    await page.getByRole('button', { name: /completar verificación/i }).click();

    await expect(page.getByText(/contraseñas no coinciden/)).toBeVisible();
  });

  test('successful verification with completed profile redirects to dashboard', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/verify/' && method === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tokens: { access: 'mock-access', refresh: 'mock-refresh' },
            user: mockPlatformClient,
          }),
        };
      }
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformClient);
      }
      if (apiPath.startsWith('accounts/projects/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    const codeInputs = page.locator('input[inputmode="numeric"]');
    for (let i = 0; i < 6; i++) {
      await codeInputs.nth(i).fill(String(i + 1));
    }

    await page.getByLabel('Nueva contraseña').fill('newpassword123');
    await page.getByLabel('Confirmar contraseña').fill('newpassword123');
    await page.getByRole('button', { name: /completar verificación/i }).click();

    await page.waitForURL('**/platform/dashboard', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });

  test('successful verification with incomplete profile redirects to complete-profile', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/verify/' && method === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
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

    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    const codeInputs = page.locator('input[inputmode="numeric"]');
    for (let i = 0; i < 6; i++) {
      await codeInputs.nth(i).fill(String(i + 1));
    }

    await page.getByLabel('Nueva contraseña').fill('newpassword123');
    await page.getByLabel('Confirmar contraseña').fill('newpassword123');
    await page.getByRole('button', { name: /completar verificación/i }).click();

    await page.waitForURL('**/platform/complete-profile', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/complete-profile/);
  });

  test('shows API error on invalid verification code', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/verify/' && method === 'POST') {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Código inválido o expirado.' }),
        };
      }
      return null;
    });

    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    const codeInputs = page.locator('input[inputmode="numeric"]');
    for (let i = 0; i < 6; i++) {
      await codeInputs.nth(i).fill('9');
    }

    await page.getByLabel('Nueva contraseña').fill('newpassword123');
    await page.getByLabel('Confirmar contraseña').fill('newpassword123');
    await page.getByRole('button', { name: /completar verificación/i }).click();

    await expect(page.getByText(/código inválido o expirado/i)).toBeVisible();
  });

  test('resend code button triggers API call and shows success message', {
    tag: [...PLATFORM_VERIFY_ONBOARDING, '@role:platform-client'],
  }, async ({ page }) => {
    let _resendCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/resend-code/' && method === 'POST') {
        _resendCalled = true;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Código reenviado exitosamente.' }),
        };
      }
      return null;
    });

    await page.goto('/platform/verify', { waitUntil: 'domcontentloaded' });

    await page.getByRole('button', { name: /reenviar código/i }).click();

    await expect(page.getByText(/reenviado exitosamente/i)).toBeVisible();
  });
});
