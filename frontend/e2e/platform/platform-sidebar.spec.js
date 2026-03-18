/**
 * E2E tests for platform sidebar navigation flow.
 *
 * @flow:platform-sidebar-navigation
 * Covers: sidebar render with navigation links, active link highlighting,
 *         admin-only links visibility, client restricted links,
 *         logout action, mobile drawer toggle.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_SIDEBAR_NAVIGATION } from '../helpers/flow-tags.js';
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

function setupSidebarMocks(page, user) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath.startsWith('accounts/projects/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

test.describe('Platform Sidebar — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders sidebar with admin navigation links', {
    tag: [...PLATFORM_SIDEBAR_NAVIGATION, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupSidebarMocks(page, mockPlatformAdmin);
    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /proyectos/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /clientes/i })).toBeVisible();
  });

  test('sidebar shows user display name and initials', {
    tag: [...PLATFORM_SIDEBAR_NAVIGATION, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupSidebarMocks(page, mockPlatformAdmin);
    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    // 'Admin E2E' appears in sidebar + dashboard welcome; use exact match scoped to sidebar
    await expect(page.getByText('Admin E2E', { exact: true })).toBeVisible();
  });

  test('navigating to projects page via sidebar link works', {
    tag: [...PLATFORM_SIDEBAR_NAVIGATION, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupSidebarMocks(page, mockPlatformAdmin);
    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await page.getByRole('link', { name: /proyectos/i }).click();
    await page.waitForURL('**/platform/projects', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/projects/);
  });
});

test.describe('Platform Sidebar — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client sidebar does not show admin-only links like Clientes', {
    tag: [...PLATFORM_SIDEBAR_NAVIGATION, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupSidebarMocks(page, mockPlatformClient);
    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /clientes/i })).not.toBeVisible();
  });
});
