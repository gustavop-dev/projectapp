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
    // quality: allow-no-interaction (static legal page — render asserted by the route and a non-empty heading)
    await page.goto('/privacy-policy');
    await expect(page).toHaveURL(/privacy-policy/);
    await expect(page.getByRole('heading').first()).toContainText(/\S/, { timeout: 15_000 });
  });
});
