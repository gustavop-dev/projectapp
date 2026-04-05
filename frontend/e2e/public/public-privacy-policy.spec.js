/**
 * E2E tests for public privacy policy page.
 *
 * @flow:public-privacy-policy
 * Covers: page renders, content visible, URL matches.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_PRIVACY_POLICY } from '../helpers/flow-tags.js';

test.describe('Privacy Policy Page', () => {
  test('renders privacy policy page with content', {
    tag: [...PUBLIC_PRIVACY_POLICY, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/privacy-policy');
    await expect(page.locator('body')).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/privacy-policy/);

    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible({ timeout: 15_000 });
  });
});
