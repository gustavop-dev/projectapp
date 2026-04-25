/**
 * E2E tests for the public blog listing page.
 *
 * Covers: blog index render, featured post hero, category filtering,
 * search, empty state, responsive mobile cards, bilingual support.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { BLOG_LIST } from '../helpers/flow-tags.js';

const mockPosts = [
  {
    id: 1,
    title: 'AI Trends 2026',
    slug: 'ai-trends-2026',
    excerpt: 'A summary of AI trends.',
    cover_image: null,
    category: 'ai',
    read_time_minutes: 8,
    is_featured: true,
    is_published: true,
    published_at: '2026-03-01T12:00:00Z',
  },
  {
    id: 2,
    title: 'Design Systems Guide',
    slug: 'design-systems-guide',
    excerpt: 'How to build a design system.',
    cover_image: null,
    category: 'design',
    read_time_minutes: 12,
    is_featured: false,
    is_published: true,
    published_at: '2026-02-20T12:00:00Z',
  },
  {
    id: 3,
    title: 'Custom Software for SMBs',
    slug: 'custom-software-smbs',
    excerpt: 'Why small businesses need custom software.',
    cover_image: null,
    category: 'business',
    read_time_minutes: 6,
    is_featured: false,
    is_published: true,
    published_at: '2026-02-15T12:00:00Z',
  },
];

function setupMock(page) {
  return mockApi(page, async ({ _route, apiPath }) => {
    if (apiPath.startsWith('blog/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPosts),
      };
    }
    return null;
  });
}

test.describe('Blog Listing', () => {
  test('renders featured post hero and post grid', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog');

    await expect(page.getByRole('heading', { name: 'Blog', level: 1 })).toBeVisible();
    await expect(page.getByText('AI Trends 2026')).toBeVisible();
    await expect(page.getByText(/Featured/)).toBeVisible();
    const grid = page.locator('.hidden.sm\\:grid');
    await expect(grid.getByText('Design Systems Guide')).toBeVisible();
    await expect(grid.getByText('Custom Software for SMBs')).toBeVisible();
  });

  test('filters posts by category', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog');

    await page.getByRole('button', { name: 'Design', exact: true }).click();

    const grid = page.locator('.hidden.sm\\:grid');
    await expect(grid.getByText('Design Systems Guide')).toBeVisible();
    await expect(grid.getByText('Custom Software for SMBs')).not.toBeVisible();
  });

  test('searches posts by text', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog');

    await page.getByPlaceholder('Search articles...').fill('Design');

    const grid = page.locator('.hidden.sm\\:grid');
    await expect(grid.getByText('Design Systems Guide')).toBeVisible();
    await expect(grid.getByText('Custom Software for SMBs')).not.toBeVisible();
  });

  test('clears filters when clicking clear button', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog');

    await page.getByPlaceholder('Search articles...').fill('nonexistent-term');

    await expect(page.getByText('No articles match')).toBeVisible();
    await page.getByText('Clear filters').click();

    const grid = page.locator('.hidden.sm\\:grid');
    await expect(grid.getByText('Design Systems Guide')).toBeVisible();
  });

  test('renders with Spanish locale', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/es-co/blog');

    await expect(page.getByRole('heading', { name: 'Blog', level: 1 })).toBeVisible();
    await expect(page.getByText(/Destacado/)).toBeVisible();
  });

  test('shows empty state when no posts', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ _route, apiPath }) => {
      if (apiPath.startsWith('blog/')) {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });
    await page.goto('/blog');

    await expect(page.getByText('No articles published yet')).toBeVisible();
  });

  test('navigates to post detail on card click', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog');

    const desktopGrid = page.locator('.hidden.sm\\:grid');
    await desktopGrid.getByText('Design Systems Guide').click();
    await expect(page).toHaveURL(/\/blog\/design-systems-guide/);
  });
});
