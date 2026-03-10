/**
 * E2E tests for public service pages.
 *
 * Covers: portfolio listing, about us, landing web design.
 * Note: web-designs, 3d-animations, hosting, e-commerce-prices, custom-software
 * were archived and are no longer accessible via navigation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PUBLIC_PORTFOLIO,
  PUBLIC_ABOUT_US,
  PUBLIC_LANDING_WEB_DESIGN,
} from '../helpers/flow-tags.js';

test.describe('Portfolio Works', () => {
  test('renders portfolio listing page', {
    tag: [...PUBLIC_PORTFOLIO, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ _route, apiPath }) => {
      if (apiPath.startsWith('portfolio/')) {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/portfolio-works');
    await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/portfolio-works/);
  });
});

test.describe('About Us', () => {
  test('renders about us page', {
    tag: [...PUBLIC_ABOUT_US, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/about-us');
    await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/about-us/);
  });
});

test.describe('Landing Web Design', () => {
  test('renders landing web design page', {
    tag: [...PUBLIC_LANDING_WEB_DESIGN, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/landing-web-design');
    await expect(page.locator('body')).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/landing-web-design/);
  });
});
