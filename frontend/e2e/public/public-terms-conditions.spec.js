/**
 * E2E tests for public terms and conditions page.
 *
 * @flow:public-terms-conditions
 * Covers: page renders, content visible, URL matches.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_TERMS_CONDITIONS } from '../helpers/flow-tags.js';

test.describe('Terms and Conditions Page', () => {
  test('renders terms and conditions page with content', {
    tag: [...PUBLIC_TERMS_CONDITIONS, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/terms-and-conditions');
    await expect(page.locator('body')).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/terms-and-conditions/);

    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });
});
