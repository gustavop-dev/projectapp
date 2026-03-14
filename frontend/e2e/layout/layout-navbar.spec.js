/**
 * E2E tests for navbar navigation.
 */
import { test, expect } from '../helpers/test.js';
import { LAYOUT_NAVBAR_NAVIGATION } from '../helpers/flow-tags.js';

test.describe('Navbar Navigation', () => {
  test('navbar is visible on home page', {
    tag: [...LAYOUT_NAVBAR_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/');

    const nav = page.getByRole('navigation', { name: 'Main navigation' });
    await expect(nav).toBeVisible({ timeout: 15000 });
    await expect(nav.getByRole('link', { name: /Custom Software|Software a la medida/i })).toBeVisible();
  });

  test('navbar is visible on subpage', {
    tag: [...LAYOUT_NAVBAR_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/blog');

    const nav = page.getByRole('navigation', { name: 'Main navigation' });
    await expect(nav).toBeVisible({ timeout: 15000 });
    await expect(nav.getByRole('link', { name: /Blog/i })).toBeVisible();
  });
});
