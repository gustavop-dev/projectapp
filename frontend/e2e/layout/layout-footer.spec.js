/**
 * E2E tests for footer navigation.
 */
import { test, expect } from '../helpers/test.js';
import { LAYOUT_FOOTER_NAVIGATION } from '../helpers/flow-tags.js';

test.describe('Footer Navigation', () => {
  test('a footer link navigates to its destination page', {
    tag: [...LAYOUT_FOOTER_NAVIGATION, '@role:guest'],
  }, async ({ page }) => {
    // Fails if the footer navigation links stop routing.
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const footer = page.getByLabel('Website footer section');
    await footer.scrollIntoViewIfNeeded();

    await footer.getByRole('link', { name: /privacidad|privacy/i }).first().click();

    await expect(page).toHaveURL(/privacy-policy/);
  });
});
