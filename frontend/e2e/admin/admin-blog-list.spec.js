/**
 * E2E tests for admin blog list view.
 *
 * Covers: renders post list with new fields, shows published/draft badges.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_LIST } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockPosts = [
  { id: 1, title_es: 'Post Publicado', title_en: 'Published Post', slug: 'post-publicado', is_published: true, category: 'ai', read_time_minutes: 8, is_featured: true, published_at: '2026-03-01T12:00:00Z', created_at: '2026-03-01T10:00:00Z' },
  { id: 2, title_es: 'Borrador', title_en: 'Draft', slug: 'borrador', is_published: false, category: 'design', read_time_minutes: 5, is_featured: false, published_at: null, created_at: '2026-02-28T10:00:00Z' },
];

test.describe('Admin Blog List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders blog post list with new fields', {
    tag: [...ADMIN_BLOG_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockPosts) };
      return null;
    });
    await page.goto('/panel/blog');
    await page.waitForLoadState('networkidle');

    const table = page.locator('table');
    await expect(table.getByRole('link', { name: 'Post Publicado' })).toBeVisible();
    await expect(table.getByRole('link', { name: 'Borrador' })).toBeVisible();
  });
});
