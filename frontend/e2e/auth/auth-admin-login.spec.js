/**
 * E2E tests for admin login flow.
 *
 * Covers: login page render, redirect to Django admin.
 */
import { test, expect } from '../helpers/test.js';
import { ADMIN_LOGIN } from '../helpers/flow-tags.js';

test.describe('Admin Login', () => {
  test('renders login page with Django Admin link', {
    tag: [...ADMIN_LOGIN, '@role:admin'],
  }, async ({ page }) => {
    await page.goto('/panel/login');

    await expect(page.locator('a[href="/admin/"]')).toBeVisible({ timeout: 15_000 });
  });
});
