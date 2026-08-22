/**
 * E2E tests for platform profile edit flow.
 *
 * @flow:platform-profile-edit
 * @flow:platform-profile-avatar-picker
 * Covers: profile page render with avatar and form fields,
 *         save changes, validation error display,
 *         cancel navigation, role badge display.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PLATFORM_PROFILE_AVATAR_PICKER,
  PLATFORM_PROFILE_EDIT,
} from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

function setupProfileMocks(page, user) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/me/' && method === 'PATCH') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...user, first_name: 'Updated' }) };
    }
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

test.describe('Platform Profile Edit — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders profile page with user data and editable fields', {
    tag: ['@outcome:display', ...PLATFORM_PROFILE_EDIT, '@role:platform-admin', '@responsive:clients'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display — profile renders the user's data and editable fields; the edit interaction is covered by the save test)
    await setupProfileMocks(page, mockPlatformAdmin);
    await page.goto('/platform/profile', { waitUntil: 'domcontentloaded' });

    const main = page.locator('main');
    await expect(main.getByText('Admin E2E')).toBeVisible();
    await expect(main.getByText('admin@e2e-test.com')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cambiar foto de perfil' })).toBeVisible();
    await expect(page.getByRole('button', { name: /guardar cambios/i })).toBeVisible();
  });

  test('opening the avatar picker keeps the image-only single-file contract', {
    tag: ['@outcome:success', ...PLATFORM_PROFILE_AVATAR_PICKER, '@role:platform-admin'],
  }, async ({ page }) => {
    // Bug caught: the accessible avatar action stopped opening the image-only single-file picker.
    // quality: allow-deep-link (the picker contract is local to the profile surface; profile navigation is covered separately)
    await setupProfileMocks(page, mockPlatformAdmin);
    await page.goto('/platform/profile', { waitUntil: 'domcontentloaded' });

    const avatarPicker = page.getByRole('button', { name: 'Cambiar foto de perfil' });
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      avatarPicker.click(),
    ]);

    const avatarInput = fileChooser.element();
    expect(await avatarInput.getAttribute('accept')).toBe('image/*');
    expect(fileChooser.isMultiple()).toBe(false);
  });

  test('saving a changed first name confirms the update', {
    tag: ['@outcome:success', ...PLATFORM_PROFILE_EDIT, '@role:platform-admin'],
  }, async ({ page }) => {
    // Bug caught: saving the profile stopped sending the edited name or stopped confirming the update.
    await setupProfileMocks(page, mockPlatformAdmin);
    await page.goto('/platform/profile', { waitUntil: 'domcontentloaded' });

    const firstNameInput = page.getByLabel('Nombre', { exact: true });
    await firstNameInput.fill('Ada');

    const updateRequest = page.waitForRequest(
      (request) => /accounts\/me\/$/.test(request.url()) && request.method() === 'PATCH',
    );
    await page.getByRole('button', { name: /guardar cambios/i }).click();
    const request = await updateRequest;

    expect(request.postDataJSON()).toMatchObject({ first_name: 'Ada' });
    await expect(page.getByText('Perfil actualizado correctamente.')).toHaveText('Perfil actualizado correctamente.');
  });

  test('shows validation error on API failure', {
    tag: ['@outcome:error', ...PLATFORM_PROFILE_EDIT, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath === 'accounts/me/' && method === 'PATCH') {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'No pudimos actualizar tu perfil.' }),
        };
      }
      if (apiPath.startsWith('accounts/clients/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/profile', { waitUntil: 'domcontentloaded' });

    await page.getByRole('button', { name: /guardar cambios/i }).click();
    await expect(page.getByText(/no pudimos actualizar/i)).toContainText(/no pudimos actualizar/i);
  });
});

test.describe('Platform Profile Edit — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client renders profile page with their data', {
    tag: ['@outcome:display', ...PLATFORM_PROFILE_EDIT, '@role:platform-client'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display — client's profile renders their data)
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupProfileMocks(page, mockPlatformClient);
    await page.goto('/platform/profile', { waitUntil: 'domcontentloaded' });

    const main = page.locator('main');
    await expect(main.getByText('Client E2E')).toBeVisible();
    await expect(main.getByText('client@e2e-test.com')).toBeVisible();
  });
});

test.describe('Platform Profile Edit — Auth guard', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('unauthenticated user is redirected to login', {
    tag: [...PLATFORM_PROFILE_EDIT, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (auth guard — an unauthenticated user is redirected to login, asserted by URL)
    await page.goto('/platform/profile', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/login**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/login/);
  });
});
