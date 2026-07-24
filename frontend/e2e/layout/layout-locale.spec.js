/**
 * E2E tests for locale switching via the navbar language toggle.
 */
import { test, expect } from '../helpers/test.js';
import { LAYOUT_LOCALE_SWITCH } from '../helpers/flow-tags.js';

test.describe('Locale Switch', () => {
  test('the language toggle switches from English to Spanish', {
    tag: [...LAYOUT_LOCALE_SWITCH, '@role:guest'],
  }, async ({ page }) => {
    // Fails if the navbar language toggle stops re-routing to the Spanish locale.
    await page.goto('/en-us');
    await expect(page).toHaveURL(/\/en-us/);

    await page.getByRole('button', { name: /Switch to Spanish/i }).first().click();

    await expect(page).toHaveURL(/\/es-co/);
  });

  test('the language toggle switches from Spanish to English', {
    tag: [...LAYOUT_LOCALE_SWITCH, '@role:guest'],
  }, async ({ page }) => {
    // Fails if the navbar language toggle stops re-routing to the English locale.
    await page.goto('/es-co');
    await expect(page).toHaveURL(/\/es-co/);

    await page.getByRole('button', { name: /Switch to English/i }).first().click();

    await expect(page).toHaveURL(/\/en-us/);
  });
});
