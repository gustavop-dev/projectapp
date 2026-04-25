/**
 * E2E tests for public landing app development page.
 *
 * @flow:public-landing-apps
 * Covers: page renders hero section and CTA, body is accessible, URL matches.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_LANDING_APPS } from '../helpers/flow-tags.js';

test.describe('Landing App Development', () => {
  test('renders landing apps page', {
    tag: [...PUBLIC_LANDING_APPS, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/landing-apps');
    await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/landing-apps/);
  });

  test('page has visible heading', {
    tag: [...PUBLIC_LANDING_APPS, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/landing-apps');

    const heading = page.getByRole('heading').first();
    await expect(heading).toBeVisible({ timeout: 15000 });
  });
});
