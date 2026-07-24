/**
 * E2E tests for public service pages.
 *
 * Covers: portfolio listing (click-through to a case study), landing web design.
 * Note: web-designs, 3d-animations, hosting, e-commerce-prices, custom-software
 * were archived and are no longer accessible via navigation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PUBLIC_PORTFOLIO,
  PUBLIC_LANDING_WEB_DESIGN,
} from '../helpers/flow-tags.js';

const mockWork = {
  id: 1,
  title: 'E-Commerce Platform Redesign',
  slug: 'ecommerce-redesign',
  excerpt: 'A complete redesign of the e-commerce experience.',
  cover_image: 'https://example.com/cover.jpg',
  is_published: true,
  published_at: '2026-03-01T12:00:00Z',
};

test.describe('Portfolio Works', () => {
  test('the portfolio listing renders published works', {
    tag: [...PUBLIC_PORTFOLIO, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — the listing renders published works fetched from the API)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath.startsWith('portfolio/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([mockWork]) };
      }
      return null;
    });

    await page.goto('/portfolio-works');
    await expect(page).toHaveURL(/portfolio-works/);
    await expect(page.getByText('E-Commerce Platform Redesign')).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Landing Web Design', () => {
  test('renders landing web design page', {
    tag: [...PUBLIC_LANDING_WEB_DESIGN, '@role:guest'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (marketing landing page — render smoke asserted by the localized route and hero heading)
    await page.goto('/landing-web-design');
    await expect(page).toHaveURL(/landing-web-design/);
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 15000 });
  });
});
