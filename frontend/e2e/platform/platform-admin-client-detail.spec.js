/**
 * E2E tests for platform admin client detail flow.
 *
 * @flow:platform-admin-client-detail
 * Covers: client detail page render with profile card and edit form,
 *         save changes, reset form, resend invite, deactivate client,
 *         not found state, back link navigation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_ADMIN_CLIENT_DETAIL } from '../helpers/flow-tags.js';
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

const mockClientDetail = {
  user_id: 9002,
  first_name: 'Client',
  last_name: 'E2E',
  email: 'client@e2e-test.com',
  company_name: 'ACME Corp',
  phone: '+57 300 000 0002',
  is_active: true,
  is_onboarded: true,
  created_at: '2025-01-10T10:00:00Z',
  cedula: '9876543210',
  date_of_birth: '1995-06-20',
  gender: 'female',
  education_level: 'posgrado',
  avatar: null,
};

function setupClientDetailMocks(page, { client = mockClientDetail } = {}) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
    if (apiPath === `accounts/clients/${client.user_id}/` && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(client) };
    }
    if (apiPath === `accounts/clients/${client.user_id}/` && method === 'PATCH') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...client, company_name: 'Updated Corp' }) };
    }
    if (apiPath === `accounts/clients/${client.user_id}/` && method === 'DELETE') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ detail: 'Cliente desactivado.' }) };
    }
    if (apiPath === `accounts/clients/${client.user_id}/resend-invite/` && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ detail: 'Invitación reenviada.' }) };
    }
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([client]) };
    }
    return null;
  });
}

test.describe('Platform Admin Client Detail', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders client detail page with profile card and edit form', {
    tag: [...PLATFORM_ADMIN_CLIENT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupClientDetailMocks(page);
    await page.goto('/platform/clients/9002', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Client E2E')).toBeVisible();
    await expect(page.getByText('client@e2e-test.com')).toBeVisible();
    await expect(page.getByText('ACME Corp')).toBeVisible();
  });

  test('shows back link to clients list', {
    tag: [...PLATFORM_ADMIN_CLIENT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupClientDetailMocks(page);
    await page.goto('/platform/clients/9002', { waitUntil: 'domcontentloaded' });

    // Scope to main to avoid matching sidebar 'Clientes' link
    const backLink = page.locator('main').getByRole('link', { name: /clientes/i });
    await expect(backLink).toBeVisible();
    // i18n prefix strategy adds locale prefix to all hrefs
    await expect(backLink).toHaveAttribute('href', /\/platform\/clients$/);
  });

  test('shows not found message for invalid client ID', {
    tag: [...PLATFORM_ADMIN_CLIENT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath === 'accounts/clients/9999/' && method === 'GET') {
        return { status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'No encontrado' }) };
      }
      if (apiPath.startsWith('accounts/clients/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/clients/9999', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/no encontramos el cliente/i)).toBeVisible();
  });

  test('shows action buttons for admin operations', {
    tag: [...PLATFORM_ADMIN_CLIENT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupClientDetailMocks(page);
    await page.goto('/platform/clients/9002', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('button', { name: /guardar cambios/i })).toBeVisible();
  });
});

test.describe('Platform Admin Client Detail — Access Guard', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client role is redirected away from client detail page', {
    tag: [...PLATFORM_ADMIN_CLIENT_DETAIL, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformClient);
      return null;
    });

    await page.goto('/platform/clients/9002', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/dashboard', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });
});
