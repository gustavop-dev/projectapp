/**
 * E2E tests for platform dashboard flow.
 *
 * @flow:platform-dashboard
 * Covers: admin dashboard render with KPI cards and recent clients table,
 *         client dashboard render with profile card and upcoming modules,
 *         unauthenticated redirect.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_DASHBOARD } from '../helpers/flow-tags.js';
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

const mockClients = [
  {
    user_id: 9002,
    first_name: 'Client',
    last_name: 'E2E',
    email: 'client@e2e-test.com',
    company_name: 'ACME Corp',
    is_active: true,
    is_onboarded: true,
    created_at: '2025-01-10T10:00:00Z',
  },
  {
    user_id: 9003,
    first_name: 'Pending',
    last_name: 'User',
    email: 'pending@e2e-test.com',
    company_name: 'Startup Inc',
    is_active: true,
    is_onboarded: false,
    created_at: '2025-01-12T10:00:00Z',
  },
];

test.describe('Platform Dashboard — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders admin dashboard with welcome message and KPI cards', {
    tag: [...PLATFORM_DASHBOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath.startsWith('accounts/clients/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockClients) };
      }
      return null;
    });

    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/hola admin/i)).toBeVisible();
    const main = page.locator('main');
    await expect(main.getByText('Clientes activos')).toBeVisible();
    await expect(main.getByText('Proyectos activos')).toBeVisible();
    await expect(main.getByText('Bugs abiertos')).toBeVisible();
  });

  test('renders recent clients table with data', {
    tag: [...PLATFORM_DASHBOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath.startsWith('accounts/clients/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockClients) };
      }
      return null;
    });

    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Clientes recientes')).toBeVisible();
    await expect(page.getByText('Client E2E')).toBeVisible();
    await expect(page.getByText('ACME Corp')).toBeVisible();
    // i18n prefix strategy adds locale prefix to all hrefs
    await expect(page.getByRole('link', { name: /ver todos/i })).toHaveAttribute('href', /\/platform\/clients$/);
  });

  test('renders empty clients state when no clients exist', {
    tag: [...PLATFORM_DASHBOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath.startsWith('accounts/clients/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/no hay clientes registrados/i)).toBeVisible();
  });
});

test.describe('Platform Dashboard — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('renders client dashboard with profile card and upcoming modules', {
    tag: [...PLATFORM_DASHBOARD, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformClient);
      return null;
    });

    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/hola client/i)).toBeVisible();
    await expect(page.getByText('Proyectos activos')).toBeVisible();
    await expect(page.getByText('Bugs abiertos')).toBeVisible();
    // 'Mis proyectos' appears in sidebar + content; scope to dashboard content area
    await expect(page.locator('#platform-dashboard').getByText('Mis proyectos')).toBeVisible();
  });
});

test.describe('Platform Dashboard — Auth guard', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('unauthenticated user is redirected to login', {
    tag: [...PLATFORM_DASHBOARD, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/login**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/login/);
  });
});
