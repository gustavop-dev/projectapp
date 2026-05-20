/**
 * E2E tests for the platform password recovery wizard.
 *
 * @flow:platform-password-reset
 * Covers: forgot-password link on login, 3-step wizard happy path with
 *         mocked endpoints, and recoverable wrong-code state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_PASSWORD_RESET } from '../helpers/flow-tags.js';

const ME_USER = {
  email: 'user@example.com',
  role: 'client',
  is_onboarded: true,
  profile_completed: true,
  user_id: 1,
  first_name: 'Test',
  last_name: 'User',
};

/**
 * Wait for Nuxt hydration so the form is interactive.
 */
const waitForForm = async (page, selector) => {
  await page.waitForLoadState('domcontentloaded');
  await page.locator(selector).waitFor({ state: 'visible', timeout: 15000 });
  // GSAP-style hydration buffer used by sibling specs.
  await page.waitForTimeout(500);
};

test.describe('Platform password recovery', () => {
  test.setTimeout(60_000);

  test(
    'happy path — login link to forgot, code accepted, new password accepted, redirect to platform',
    { tag: PLATFORM_PASSWORD_RESET },
    async ({ page }) => {
      await mockApi(page, async ({ apiPath, method }) => {
        if (method === 'POST' && apiPath === 'accounts/password-reset/request/') {
          return {
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ reset_request_token: 'mock-request-token' }),
          };
        }
        if (method === 'POST' && apiPath === 'accounts/password-reset/verify-code/') {
          return {
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ reset_verified_token: 'mock-verified-token' }),
          };
        }
        if (method === 'POST' && apiPath === 'accounts/password-reset/confirm/') {
          return {
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              access: 'mock-access',
              refresh: 'mock-refresh',
              user: ME_USER,
            }),
          };
        }
        if (method === 'GET' && apiPath === 'accounts/me/') {
          return { status: 200, contentType: 'application/json', body: JSON.stringify(ME_USER) };
        }
        return null;
      });

      await page.goto('/es-co/platform/login', { waitUntil: 'domcontentloaded' });
      await waitForForm(page, 'a:has-text("Olvidaste tu contraseña")');
      await page.getByRole('link', { name: /Olvidaste tu contraseña/i }).click();

      // Page-specific selectors per step: login and forgot-password both expose
      // input[type=email] / button[type=submit], so generic selectors can race
      // the SPA transition and act on the wrong page.
      await page.waitForURL(/\/platform\/forgot-password/, { waitUntil: 'domcontentloaded' });
      await waitForForm(page, '#forgot-email');
      await page.locator('#forgot-email').fill('user@example.com');
      await page.getByRole('button', { name: 'Enviar código' }).click();

      await page.waitForURL(/\/platform\/verify-code/, { waitUntil: 'domcontentloaded' });
      await waitForForm(page, 'input[name="otp"]');
      await page.locator('input[name="otp"]').fill('123456');
      await page.getByRole('button', { name: 'Verificar' }).click();

      await page.waitForURL(/\/platform\/reset-password/, { waitUntil: 'domcontentloaded' });
      await waitForForm(page, '#new-pass');
      await page.locator('#new-pass').fill('NewStrongPass456!');
      await page.locator('#confirm-pass').fill('NewStrongPass456!');
      await page.getByRole('button', { name: 'Guardar contraseña' }).click();

      // Successful confirm: store applies auth + navigates to /platform.
      await page.waitForURL(/\/platform(\?|$|\/(?!forgot|verify|reset))/, {
        waitUntil: 'domcontentloaded',
      });
    },
  );

  test(
    'wrong code surfaces attempts_left and stays on verify-code',
    { tag: PLATFORM_PASSWORD_RESET },
    async ({ page }) => {
      await mockApi(page, async ({ apiPath, method }) => {
        if (method === 'POST' && apiPath === 'accounts/password-reset/request/') {
          return {
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ reset_request_token: 'mock-request-token' }),
          };
        }
        if (method === 'POST' && apiPath === 'accounts/password-reset/verify-code/') {
          return {
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'invalid_code', attempts_left: 3 }),
          };
        }
        return null;
      });

      await page.goto('/es-co/platform/forgot-password', { waitUntil: 'domcontentloaded' });
      await waitForForm(page, 'input[type="email"]');
      await page.locator('input[type="email"]').fill('user@example.com');
      await page.locator('button[type="submit"]').click();
      await page.waitForURL(/\/platform\/verify-code/, { waitUntil: 'domcontentloaded' });

      await waitForForm(page, 'input[name="otp"]');
      await page.locator('input[name="otp"]').fill('000000');
      await page.locator('button[type="submit"]').click();

      await expect(page.getByText(/3 intentos/i)).toBeVisible({ timeout: 10000 });
      expect(page.url()).toContain('/platform/verify-code');
    },
  );
});
