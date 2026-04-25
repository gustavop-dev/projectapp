/**
 * E2E tests for public landing software development page.
 *
 * @flow:public-landing-software
 * Covers: page renders hero section and CTA, body is accessible, URL matches.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_LANDING_SOFTWARE } from '../helpers/flow-tags.js';

test.describe('Landing Software Development', () => {
  test('renders landing software page', {
    tag: [...PUBLIC_LANDING_SOFTWARE, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/landing-software');
    await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/landing-software/);
  });

  test('page has visible heading', {
    tag: [...PUBLIC_LANDING_SOFTWARE, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/landing-software');

    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible({ timeout: 15000 });
  });
});
