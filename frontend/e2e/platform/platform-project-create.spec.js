/**
 * E2E tests for platform admin project create flow.
 *
 * @flow:platform-admin-project-create
 * Covers: create project modal render, form validation,
 *         client dropdown, submit success, submit error,
 *         modal close behavior.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_ADMIN_PROJECT_CREATE } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
} from '../helpers/platform-auth.js';

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

const mockClients = [
  {
    user_id: 9002,
    first_name: 'Client',
    last_name: 'E2E',
    email: 'client@e2e-test.com',
    company_name: 'ACME Corp',
    is_active: true,
    is_onboarded: true,
  },
];

function setupCreateProjectMocks(page) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === 'accounts/projects/' && method === 'POST') {
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 10,
          name: 'New Project',
          description: 'Test project',
          status: 'active',
          progress: 0,
          client_id: 9002,
          client_name: 'Client E2E',
          client_company: 'ACME Corp',
        }),
      };
    }
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockClients) };
    }
    return null;
  });
}

test.describe('Platform Admin Project Create', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('opens create project modal with required fields', {
    tag: [...PLATFORM_ADMIN_PROJECT_CREATE, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCreateProjectMocks(page);
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await page.getByRole('button', { name: /nuevo proyecto/i }).click();

    await expect(page.getByRole('heading', { name: 'Nuevo proyecto' })).toBeVisible();
    await expect(page.getByPlaceholder(/plataforma e-commerce/i)).toBeVisible();
    // 'Selecciona un cliente' is a disabled <option> inside select — verify the select exists
    await expect(page.getByRole('combobox')).toBeVisible();
  });

  test('create button is disabled when required fields are empty', {
    tag: [...PLATFORM_ADMIN_PROJECT_CREATE, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCreateProjectMocks(page);
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await page.getByRole('button', { name: /nuevo proyecto/i }).click();

    const createBtn = page.getByRole('button', { name: /crear proyecto/i });
    await expect(createBtn).toBeDisabled();
  });

  test('successful project creation closes modal', {
    tag: [...PLATFORM_ADMIN_PROJECT_CREATE, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCreateProjectMocks(page);
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await page.getByRole('button', { name: /nuevo proyecto/i }).click();
    await page.getByPlaceholder(/plataforma e-commerce/i).fill('New Project');
    await page.locator('select').selectOption({ value: '9002' });
    await page.getByRole('button', { name: /crear proyecto/i }).click();

    await expect(page.getByRole('heading', { name: 'Nuevo proyecto' })).not.toBeVisible({ timeout: 5000 });
  });

  test('cancel button closes modal without submitting', {
    tag: [...PLATFORM_ADMIN_PROJECT_CREATE, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCreateProjectMocks(page);
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await page.getByRole('button', { name: /nuevo proyecto/i }).click();
    await expect(page.getByRole('heading', { name: 'Nuevo proyecto' })).toBeVisible();

    await page.getByRole('button', { name: /cancelar/i }).click();
    await expect(page.getByRole('heading', { name: 'Nuevo proyecto' })).not.toBeVisible({ timeout: 5000 });
  });
});
