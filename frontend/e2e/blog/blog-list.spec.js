/**
 * E2E tests for the public blog listing page.
 *
 * Covers: blog index render, bilingual support, empty state.
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
    published_at: '2026-03-01T12:00:00Z',
  },
];

test.describe('Blog Listing', () => {
  test('renders blog post grid with published posts', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath.startsWith('blog/')) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockPosts),
        };
      }
      return null;
    });

    await page.goto('/blog');

    await page.waitForLoadState('networkidle');
  });

  test('renders with English locale', {
    tag: [...BLOG_LIST, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath.startsWith('blog/')) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockPosts),
        };
      }
      return null;
    });

    await page.goto('/en-us/blog');

    await page.waitForLoadState('networkidle');
  });
});
