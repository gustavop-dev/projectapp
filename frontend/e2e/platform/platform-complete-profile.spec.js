/**
 * E2E tests for platform complete-profile flow.
 *
 * @flow:platform-complete-profile
 * Covers: form render with required fields, submit with valid data,
 *         validation errors, redirect to dashboard on success,
 *         redirect to login when unauthenticated,
 *         redirect to dashboard when profile already completed.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_COMPLETE_PROFILE } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClientIncompleteProfile,
} from '../helpers/platform-auth.js';

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

test.describe('Platform Complete Profile', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('renders complete-profile form with all required fields', {
    tag: [...PLATFORM_COMPLETE_PROFILE, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClientIncompleteProfile });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformClientIncompleteProfile);
      }
      return null;
    });

    await page.goto('/platform/complete-profile', { waitUntil: 'domcontentloaded' });
    await page.getByText('Completa tu perfil').waitFor({ state: 'visible', timeout: 15000 });
    await expect(page.getByPlaceholder('Nombre de tu empresa')).toBeVisible();
    await expect(page.getByPlaceholder(/300 000 0000/)).toBeVisible();
    await expect(page.getByPlaceholder('1020304050')).toBeVisible();
    await expect(page.getByRole('button', { name: /completar perfil/i })).toBeVisible();
  });

  test('submit button is disabled when required fields are empty', {
    tag: [...PLATFORM_COMPLETE_PROFILE, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClientIncompleteProfile });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformClientIncompleteProfile);
      }
      return null;
    });

    await page.goto('/platform/complete-profile', { waitUntil: 'domcontentloaded' });
    await page.getByText('Completa tu perfil').waitFor({ state: 'visible', timeout: 15000 });

    const submitBtn = page.getByRole('button', { name: /completar perfil/i });
    await expect(submitBtn).toBeDisabled();
  });

  test('successful profile completion redirects to dashboard', {
    tag: [...PLATFORM_COMPLETE_PROFILE, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClientIncompleteProfile });

    const completedUser = {
      ...mockPlatformClientIncompleteProfile,
      first_name: 'Client',
      last_name: 'Test',
      company_name: 'Test Corp',
      phone: '+57 300 111 2222',
      cedula: '1234567890',
      date_of_birth: '1992-03-15',
      gender: 'female',
      education_level: 'universitario',
      profile_completed: true,
    };

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformClientIncompleteProfile);
      }
      if (apiPath === 'accounts/me/complete-profile/' && method === 'POST') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(completedUser) };
      }
      return null;
    });

    await page.goto('/platform/complete-profile', { waitUntil: 'domcontentloaded' });
    await page.getByText('Completa tu perfil').waitFor({ state: 'visible', timeout: 15000 });

    await page.getByPlaceholder('Tu nombre').fill('Client');
    await page.getByPlaceholder('Tu apellido').fill('Test');
    await page.getByPlaceholder('Nombre de tu empresa').fill('Test Corp');
    await page.getByPlaceholder(/300 000 0000/).fill('+57 300 111 2222');
    await page.getByPlaceholder('1020304050').fill('1234567890');
    await page.getByTestId('date-of-birth').fill('1992-03-15');
    await page.getByTestId('gender-select').selectOption('female');
    await page.getByTestId('education-select').selectOption('universitario');

    await page.getByRole('button', { name: /completar perfil/i }).click();

    await page.waitForURL('**/platform/dashboard', { timeout: 15000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });

  test('shows error on API failure', {
    tag: [...PLATFORM_COMPLETE_PROFILE, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClientIncompleteProfile });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformClientIncompleteProfile);
      }
      if (apiPath === 'accounts/me/complete-profile/' && method === 'POST') {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'No pudimos completar tu perfil.' }),
        };
      }
      return null;
    });

    await page.goto('/platform/complete-profile', { waitUntil: 'domcontentloaded' });
    await page.getByText('Completa tu perfil').waitFor({ state: 'visible', timeout: 15000 });

    await page.getByPlaceholder('Nombre de tu empresa').fill('Corp');
    await page.getByPlaceholder(/300 000 0000/).fill('+57 300 111 2222');
    await page.getByPlaceholder('1020304050').fill('1234567890');
    await page.getByTestId('date-of-birth').fill('1992-03-15');
    await page.getByTestId('gender-select').selectOption('male');
    await page.getByTestId('education-select').selectOption('tecnico');

    await page.getByRole('button', { name: /completar perfil/i }).click();

    await expect(page.getByText(/no pudimos completar tu perfil/i)).toBeVisible();
  });

  test('unauthenticated user is redirected to login', {
    tag: [...PLATFORM_COMPLETE_PROFILE, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/platform/complete-profile', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/login**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/login/);
  });

  test('user with completed profile is redirected to dashboard', {
    tag: [...PLATFORM_COMPLETE_PROFILE, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') {
        return meResponse(mockPlatformAdmin);
      }
      if (apiPath === 'accounts/clients/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/complete-profile', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/dashboard', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });
});
