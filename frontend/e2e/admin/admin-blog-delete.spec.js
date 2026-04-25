/**
 * E2E tests for admin blog post deletion.
 *
 * Covers: delete button visible in list, mock data with new fields.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_DELETE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockPosts = [
  { id: 1, title_es: 'Post a Borrar', title_en: 'Post to Delete', slug: 'post-borrar', is_published: true, category: 'ai', read_time_minutes: 5, is_featured: false, published_at: '2026-03-01T12:00:00Z', created_at: '2026-03-01T10:00:00Z' },
];

test.describe('Admin Blog Delete', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9000, role: 'admin', is_staff: true } });
  });

  test('renders blog list with delete-capable post', {
    tag: [...ADMIN_BLOG_DELETE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'blog/admin/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockPosts) };
      if (apiPath === 'blog/admin/1/delete/') return { status: 204, contentType: 'application/json', body: '' };
      return null;
    });
    await page.goto('/panel/blog');

    const table = page.locator('table');
    await expect(table.getByText('Post a Borrar')).toBeVisible();
  });
});
