/**
 * E2E tests for footer navigation.
 */
import { test, expect } from '../helpers/test.js';
import { LAYOUT_FOOTER_NAVIGATION } from '../helpers/flow-tags.js';

test.describe('Footer Navigation', () => {
  test('footer is visible on home page', {
    tag: [...LAYOUT_FOOTER_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.locator('footer').first()).toBeAttached();
  });
});
