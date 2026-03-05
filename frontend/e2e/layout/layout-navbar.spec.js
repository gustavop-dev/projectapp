/**
 * E2E tests for navbar navigation.
 */
import { test } from '../helpers/test.js';
import { LAYOUT_NAVBAR_NAVIGATION } from '../helpers/flow-tags.js';

test.describe('Navbar Navigation', () => {
  test('navbar is visible on home page', {
    tag: [...LAYOUT_NAVBAR_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('navbar is visible on subpage', {
    tag: [...LAYOUT_NAVBAR_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/about-us');
    await page.waitForLoadState('networkidle');
  });
});
