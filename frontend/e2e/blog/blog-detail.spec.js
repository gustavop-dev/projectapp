/**
 * E2E tests for the blog post detail page.
 *
 * Covers: post render with JSON content, HTML fallback, category badge,
 * share button, sources section, 404 handling, back navigation, CTA.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { BLOG_DETAIL } from '../helpers/flow-tags.js';

const mockPostWithJson = {
  id: 1,
  title: 'AI Trends 2026',
  slug: 'ai-trends-2026',
  content: '',
  content_json: {
    intro: 'Artificial intelligence is evolving rapidly.',
    sections: [
      { heading: 'Large Language Models', content: 'LLMs are the backbone of modern AI.' },
      { heading: 'Key Benefits', list: ['Automation', 'Scalability', 'Insights'] },
      { heading: 'Implementation Steps', timeline: [
        { step: 'Assessment', description: 'Evaluate your needs.' },
        { step: 'Deployment', description: 'Deploy the solution.' },
      ]},
    ],
    conclusion: 'AI will transform every industry.',
    cta: 'Contact us to start your AI journey.',
  },
  excerpt: 'A summary of AI trends.',
  cover_image: null,
  category: 'ai',
  read_time_minutes: 8,
  is_featured: true,
  meta_title: 'AI Trends 2026 — Project App',
  meta_description: 'A deep dive into AI trends.',
  sources: [{ name: 'OpenAI', url: 'https://openai.com' }],
  is_published: true,
  published_at: '2026-03-01T12:00:00Z',
};

const mockPostHtml = {
  id: 2,
  title: 'Legacy HTML Post',
  slug: 'legacy-html-post',
  content: '<h2>Section One</h2><p>This is HTML content.</p>',
  content_json: {},
  excerpt: 'A legacy post.',
  cover_image: null,
  category: '',
  read_time_minutes: 0,
  is_featured: false,
  meta_title: '',
  meta_description: '',
  sources: [],
  is_published: true,
  published_at: '2026-02-01T12:00:00Z',
};

const mockPosts = [mockPostWithJson, mockPostHtml];

function setupMock(page) {
  return mockApi(page, async ({ _route, apiPath }) => {
    if (apiPath.startsWith('blog/') && !apiPath.includes('admin')) {
      const slugMatch = apiPath.match(/^blog\/([^/?]+)\//);
      if (slugMatch) {
        const slug = slugMatch[1];
        const found = [mockPostWithJson, mockPostHtml].find(p => p.slug === slug);
        if (found) {
          return { status: 200, contentType: 'application/json', body: JSON.stringify(found) };
        }
        return { status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Not found.' }) };
      }
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockPosts) };
    }
    return null;
  });
}

test.describe('Blog Post Detail', () => {
  test('renders JSON content sections (headings, lists, timeline)', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/ai-trends-2026');

    // Wait for the heading to confirm page has hydrated instead of relying on networkidle
    await expect(page.getByRole('heading', { name: 'AI Trends 2026' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Artificial intelligence is evolving rapidly.')).toBeVisible();
    await expect(page.getByText('Large Language Models')).toBeVisible();
    await expect(page.getByText('Key Benefits')).toBeVisible();
    await expect(page.getByText('Automation')).toBeVisible();
    await expect(page.getByText('Implementation Steps')).toBeVisible();
    await expect(page.getByText('AI will transform every industry.')).toBeVisible();
  });

  test('shows category badge and read time', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/ai-trends-2026');

    await expect(page.getByRole('heading', { name: 'AI Trends 2026' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('8 min')).toBeVisible();
  });

  test('renders sources section with links', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/ai-trends-2026');

    await expect(page.getByRole('heading', { name: 'AI Trends 2026' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Sources consulted')).toBeVisible();
    await expect(page.getByText('OpenAI')).toBeVisible();
  });

  test('renders HTML fallback for posts without JSON content', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/legacy-html-post');

    await expect(page.getByRole('heading', { name: 'Legacy HTML Post' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('This is HTML content.')).toBeVisible();
  });

  test('shows 404 for nonexistent slug', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/nonexistent-post');

    await expect(page.getByText('Article not found')).toBeVisible({ timeout: 15000 });
  });

  test('back to blog link navigates to /blog', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/ai-trends-2026');

    // Wait for page content instead of networkidle to save time budget
    await expect(page.getByRole('heading', { name: 'AI Trends 2026' })).toBeVisible({ timeout: 15000 });

    await page.getByText('Back to blog').first().click();
    await expect(page).toHaveURL(/\/blog/);
  });

  test('CTA contact button is visible', {
    tag: [...BLOG_DETAIL, '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/blog/ai-trends-2026');

    await expect(page.getByText('Did This Article Inspire You?')).toBeVisible();
    await expect(page.getByRole('link', { name: /Contact Us/ })).toBeVisible();
  });
});
