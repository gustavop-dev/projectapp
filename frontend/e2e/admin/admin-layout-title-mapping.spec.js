/**
 * E2E tests for admin layout browser tab title mapping.
 *
 * @flow:admin-layout-title-mapping
 * Covers: static exact match (dashboard), static prefix match, more-specific
 * static route taking priority over prefix, and dynamic regex route matching.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_LAYOUT_TITLE_MAPPING } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

test.describe('Admin Layout — Browser Tab Title', () => {
  test.setTimeout(120_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9000, role: 'admin', is_staff: true },
    });
  });

  test('shows "Dashboard" on /panel — exact match guard prevents prefix leakage', {
    tag: [...ADMIN_LAYOUT_TITLE_MAPPING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Dashboard\)/, { timeout: 10_000 });
  });

  test('shows "Propuestas" on /panel/proposals', {
    tag: [...ADMIN_LAYOUT_TITLE_MAPPING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Propuestas\)/, { timeout: 10_000 });
  });

  test('shows "Nueva prop." on /panel/proposals/create — more-specific route beats /panel/proposals prefix', {
    tag: [...ADMIN_LAYOUT_TITLE_MAPPING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/proposals/create', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Nueva prop\.\)/, { timeout: 10_000 });
  });

  test('shows "Edit. propuesta" on /panel/proposals/:id/edit — dynamic regex route', {
    tag: [...ADMIN_LAYOUT_TITLE_MAPPING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/proposals/999/edit', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Edit\. propuesta\)/, { timeout: 10_000 });
  });

  test('shows "Calendario" on /panel/blog/calendar — nested route beats /panel/blog prefix', {
    tag: [...ADMIN_LAYOUT_TITLE_MAPPING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/blog/calendar', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveTitle(/Project App \(Calendario\)/, { timeout: 10_000 });
  });
});
