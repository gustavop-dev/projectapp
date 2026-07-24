/**
 * E2E tests for public landing app development page.
 *
 * @flow:public-landing-apps
 * Covers: page renders hero section, URL matches.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_LANDING_APPS } from '../helpers/flow-tags.js';

test.describe('Landing App Development', () => {
  test('renders the landing apps page with its heading', {
    tag: [...PUBLIC_LANDING_APPS, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (marketing landing page — render asserted by the route and a non-empty heading)
    await page.goto('/landing-apps');
    await expect(page).toHaveURL(/landing-apps/);
    await expect(page.getByRole('heading').first()).toContainText(/\S/, { timeout: 15000 });
  });
});
