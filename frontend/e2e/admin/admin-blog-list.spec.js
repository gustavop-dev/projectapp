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

const paginatedResponse = { results: mockPosts, count: 2, page: 1, page_size: 15, total_pages: 1 };
const multiPageResponse = {
  results: mockPosts,
  count: 20,
  page: 1,
  page_size: 2,
  total_pages: 10,
};

test.describe('Admin Blog List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders blog post list with new fields', {
    tag: [...ADMIN_BLOG_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/')) return { status: 200, contentType: 'application/json', body: JSON.stringify(paginatedResponse) };
      return null;
    });
    await page.goto('/panel/blog');

    const table = page.locator('table');
    await expect(table.getByRole('link', { name: 'Post Publicado' })).toBeVisible();
    await expect(table.getByRole('link', { name: 'Borrador' })).toBeVisible();
  });

  test('shows pagination controls when total pages exceeds 1', {
    tag: [...ADMIN_BLOG_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/')) return { status: 200, contentType: 'application/json', body: JSON.stringify(multiPageResponse) };
      return null;
    });
    await page.goto('/panel/blog');

    const pagination = page.getByRole('navigation', { name: 'Paginación' });
    await expect(pagination).toBeVisible();
    await expect(pagination.getByText(/de\s*20/)).toBeVisible();
    await expect(pagination.getByRole('button', { name: /Página anterior/i })).toBeVisible();
    await expect(pagination.getByRole('button', { name: /Página siguiente/i })).toBeVisible();
  });

  test('calendar link navigates to calendar page', {
    tag: [...ADMIN_BLOG_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/')) return { status: 200, contentType: 'application/json', body: JSON.stringify(paginatedResponse) };
      return null;
    });
    await page.goto('/panel/blog');

    const calendarLink = page.getByRole('link', { name: 'Calendario' });
    await expect(calendarLink).toBeVisible();
    await expect(calendarLink).toHaveAttribute('href', /\/panel\/blog\/calendar/);
  });
});
