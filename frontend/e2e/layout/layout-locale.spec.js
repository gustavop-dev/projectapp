/**
 * E2E tests for locale switching.
 */
import { test, expect } from '../helpers/test.js';
import { LAYOUT_LOCALE_SWITCH } from '../helpers/flow-tags.js';

test.describe('Locale Switch', () => {
  test('page renders with Spanish locale prefix', {
    tag: [...LAYOUT_LOCALE_SWITCH, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/es-co');
    await expect(page).toHaveURL(/\/es-co/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('page renders with English locale prefix', {
    tag: [...LAYOUT_LOCALE_SWITCH, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/en-us');
    await expect(page).toHaveURL(/\/en-us/);
    await expect(page.locator('body')).toBeVisible();
  });
});
