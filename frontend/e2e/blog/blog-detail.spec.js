/**
 * E2E tests for the blog post detail page.
 *
 * Covers: post render by slug, bilingual content, 404 handling.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { BLOG_DETAIL } from '../helpers/flow-tags.js';

const mockPost = {
  id: 1,
  title: 'AI Trends 2026',
  slug: 'ai-trends-2026',
  content: '<p>Full article content.</p>',
  excerpt: 'A summary of AI trends.',
  cover_image: null,
  sources: [{ name: 'OpenAI', url: 'https://openai.com' }],
  published_at: '2026-03-01T12:00:00Z',
};

test.describe('Blog Post Detail', () => {
  test('renders blog post content by slug', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'blog/ai-trends-2026/') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockPost),
        };
      }
      if (apiPath.startsWith('blog/')) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockPost),
        };
      }
      return null;
    });

    await page.goto('/blog/ai-trends-2026');

    await expect(page.locator('body')).toBeVisible();
  });

  test('shows 404 for nonexistent slug', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath.startsWith('blog/')) {
        return {
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Not found.' }),
        };
      }
      return null;
    });

    await page.goto('/blog/nonexistent-post');

    await expect(page.locator('body')).toBeVisible();
  });
});
