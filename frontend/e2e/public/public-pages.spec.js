/**
 * E2E tests for public service pages.
 *
 * Covers: portfolio, web designs, 3D animations, hosting, e-commerce,
 * custom software, about us, landing web design.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import {
  PUBLIC_PORTFOLIO,
  PUBLIC_WEB_DESIGNS,
  PUBLIC_3D_ANIMATIONS,
  PUBLIC_HOSTING,
  PUBLIC_ECOMMERCE_PRICES,
  PUBLIC_CUSTOM_SOFTWARE,
  PUBLIC_ABOUT_US,
  PUBLIC_LANDING_WEB_DESIGN,
} from '../helpers/flow-tags.js';

test.describe('Portfolio Works', () => {
  test('renders portfolio page', {
    tag: [...PUBLIC_PORTFOLIO, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'portfolio_works/') {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/portfolio-works');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Web Designs', () => {
  test('renders web designs page', {
    tag: [...PUBLIC_WEB_DESIGNS, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'designs/') {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/web-designs');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('3D Animations', () => {
  test('renders 3D animations page', {
    tag: [...PUBLIC_3D_ANIMATIONS, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'models3d/') {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/3d-animations');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Hosting Plans', () => {
  test('renders hosting page', {
    tag: [...PUBLIC_HOSTING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'hostings/') {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/hosting');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('E-Commerce Prices', () => {
  test('renders e-commerce pricing page', {
    tag: [...PUBLIC_ECOMMERCE_PRICES, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'products/') {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/e-commerce-prices');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Custom Software', () => {
  test('renders custom software page', {
    tag: [...PUBLIC_CUSTOM_SOFTWARE, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/custom-software');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('About Us', () => {
  test('renders about us page', {
    tag: [...PUBLIC_ABOUT_US, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/about-us');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Landing Web Design', () => {
  test('renders landing web design page', {
    tag: [...PUBLIC_LANDING_WEB_DESIGN, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/landing-web-design');
    await expect(page.locator('body')).toBeVisible();
  });
});
