/**
 * E2E tests for platform layout browser tab title mapping.
 *
 * @flow:platform-layout-title-mapping
 * Covers: static route, dynamic project base route, and nested dynamic route
 * (board within project) where more-specific regex must win over project base.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setPlatformAuth, mockPlatformAdmin } from '../helpers/platform-auth.js';
import { PLATFORM_LAYOUT_TITLE_MAPPING } from '../helpers/flow-tags.js';

const meResponse = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(mockPlatformAdmin),
};

test.describe('Platform Layout — Browser Tab Title', () => {
  test.setTimeout(120_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('shows "Dashboard" on /platform/dashboard', {
    tag: [...PLATFORM_LAYOUT_TITLE_MAPPING, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'accounts/me/') return meResponse;
      return null;
    });
    await page.goto('/platform/dashboard', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Dashboard\)/, { timeout: 10_000 });
  });

  test('shows "Proyectos" on /platform/projects', {
    tag: [...PLATFORM_LAYOUT_TITLE_MAPPING, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'accounts/me/') return meResponse;
      return null;
    });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Proyectos\)/, { timeout: 10_000 });
  });

  test('shows "Proyecto" on /platform/projects/:id — dynamic regex route', {
    tag: [...PLATFORM_LAYOUT_TITLE_MAPPING, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'accounts/me/') return meResponse;
      return null;
    });
    await page.goto('/platform/projects/1', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Proyecto\)/, { timeout: 10_000 });
  });

  test('shows "Tablero" on /platform/projects/:id/board — nested dynamic regex beats project base', {
    tag: [...PLATFORM_LAYOUT_TITLE_MAPPING, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'accounts/me/') return meResponse;
      return null;
    });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Tablero\)/, { timeout: 10_000 });
  });
});
