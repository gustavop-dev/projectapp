/**
 * E2E tests for public landing software development page.
 *
 * @flow:public-landing-software
 * Covers: page renders hero section, URL matches.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_LANDING_SOFTWARE } from '../helpers/flow-tags.js';

test.describe('Landing Software Development', () => {
  test('renders the landing software page with its heading', {
    tag: [...PUBLIC_LANDING_SOFTWARE, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (marketing landing page — render asserted by the route and a non-empty heading)
    await page.goto('/landing-software');
    await expect(page).toHaveURL(/landing-software/);
    await expect(page.getByRole('heading').first()).toContainText(/\S/, { timeout: 15000 });
  });
});
