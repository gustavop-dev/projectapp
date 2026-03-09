/**
 * E2E tests for the public portfolio case study detail page.
 *
 * Covers: renders case study with content sections, back navigation,
 * 404 for nonexistent slug, share button, visit site link, CTA section.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PUBLIC_PORTFOLIO_DETAIL } from '../helpers/flow-tags.js';

const mockWork = {
  id: 1,
  title: 'E-Commerce Platform Redesign',
  slug: 'ecommerce-redesign',
  excerpt: 'A complete redesign of the e-commerce experience.',
  cover_image: 'https://example.com/cover.jpg',
  project_url: 'https://example-client.com',
  content_json: {
    problem: {
      title: 'The Challenge',
      description: 'The existing platform had poor UX and slow load times.',
      highlights: ['High bounce rate', 'Low conversion'],
    },
    solution: {
      title: 'Our Solution',
      description: 'We rebuilt the platform with modern technologies.',
      highlights: ['Nuxt 3 frontend', 'Django REST backend'],
    },
    results: {
      title: 'The Results',
      description: 'Conversion rate increased by 45%.',
      highlights: ['45% more conversions', '2x faster load time'],
    },
  },
  meta_title: 'E-Commerce Redesign — Project App',
  meta_description: 'Case study of a full e-commerce redesign.',
  is_published: true,
  published_at: '2026-03-01T12:00:00Z',
};

const mockWorks = [mockWork];

function setupMock(page) {
  return mockApi(page, async ({ _route, apiPath }) => {
    if (apiPath.startsWith('portfolio/')) {
      const slugMatch = apiPath.match(/^portfolio\/([^/?]+)\//);
      if (slugMatch) {
        const slug = slugMatch[1];
        if (slug === mockWork.slug) {
          return { status: 200, contentType: 'application/json', body: JSON.stringify(mockWork) };
        }
        return { status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Not found.' }) };
      }
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockWorks) };
    }
    return null;
  });
}

test.describe('Portfolio Case Study Detail', () => {
  test('renders case study with title, excerpt, and content sections', {
    tag: [...PUBLIC_PORTFOLIO_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/portfolio-works/ecommerce-redesign');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'E-Commerce Platform Redesign' })).toBeVisible();
    await expect(page.getByText('A complete redesign of the e-commerce experience.')).toBeVisible();
    await expect(page.getByText('The Challenge')).toBeVisible();
    await expect(page.getByText('The existing platform had poor UX and slow load times.')).toBeVisible();
    await expect(page.getByText('Our Solution')).toBeVisible();
    await expect(page.getByText('The Results')).toBeVisible();
  });

  test('shows back link to portfolio listing', {
    tag: [...PUBLIC_PORTFOLIO_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/portfolio-works/ecommerce-redesign');
    await page.waitForLoadState('networkidle');

    const backLink = page.getByText('All projects');
    await expect(backLink).toBeVisible();
  });

  test('shows visit site link when project_url exists', {
    tag: [...PUBLIC_PORTFOLIO_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/portfolio-works/ecommerce-redesign');
    await page.waitForLoadState('networkidle');

    const visitLink = page.getByRole('article').getByRole('link', { name: /Visit Site/ });
    await expect(visitLink).toBeVisible();
    await expect(visitLink).toHaveAttribute('href', 'https://example-client.com');
  });

  test('shows 404 for nonexistent slug', {
    tag: [...PUBLIC_PORTFOLIO_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/portfolio-works/nonexistent-project');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Project not found')).toBeVisible();
    await expect(page.getByRole('link', { name: /Back to portfolio/ })).toBeVisible();
  });

  test('CTA section is visible', {
    tag: [...PUBLIC_PORTFOLIO_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/portfolio-works/ecommerce-redesign');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Ready to Build Something Like This?')).toBeVisible();
    await expect(page.getByRole('link', { name: /Get a Quote/ })).toBeVisible();
  });
});
