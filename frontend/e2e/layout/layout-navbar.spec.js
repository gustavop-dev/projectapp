/**
 * E2E tests for navbar navigation.
 */
import { test, expect } from '../helpers/test.js';
import { LAYOUT_NAVBAR_NAVIGATION } from '../helpers/flow-tags.js';

test.describe('Navbar Navigation', () => {
  test('clicking Blog in the navbar opens the blog listing', {
    tag: [...LAYOUT_NAVBAR_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    // Fails if the navbar Blog link stops routing to the blog listing.
    await page.goto('/');
    const nav = page.getByRole('navigation', { name: 'Main navigation' });
    await expect(nav).toBeVisible({ timeout: 15000 });

    await nav.getByRole('link', { name: /Blog/i }).click();

    await expect(page).toHaveURL(/\/blog/);
  });

  test('the main navigation landmark is present on subpages', {
    tag: [...LAYOUT_NAVBAR_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (landmark-presence smoke; navbar navigation is exercised by the Blog-link test above)
    await page.goto('/blog');
    const nav = page.getByRole('navigation', { name: 'Main navigation' });
    await expect(nav).toBeVisible({ timeout: 15000 });
    await expect(nav.getByRole('link', { name: /Blog/i })).toBeVisible();
  });
});
