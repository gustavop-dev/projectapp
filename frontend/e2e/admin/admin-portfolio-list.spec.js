/**
 * E2E tests for admin portfolio works list.
 *
 * Covers: renders portfolio list with works, shows empty state,
 * shows create link, displays status badges.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PORTFOLIO_LIST } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockWorks = [
  { id: 1, title_es: 'Proyecto Web', title_en: 'Web Project', slug: 'proyecto-web', is_published: true, order: 1, published_at: '2026-03-01T12:00:00Z', created_at: '2026-03-01T10:00:00Z' },
  { id: 2, title_es: 'App Móvil', title_en: 'Mobile App', slug: 'app-movil', is_published: false, order: 2, published_at: null, created_at: '2026-02-28T10:00:00Z' },
];

function setupMock(page, { works = mockWorks } = {}) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'portfolio/admin/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(works) };
    }
    return null;
  });
}

test.describe('Admin Portfolio List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9100, role: 'admin', is_staff: true } });
  });

  test('renders portfolio works list with titles and status badges', {
    tag: [...ADMIN_PORTFOLIO_LIST, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio');
    await page.waitForLoadState('networkidle');

    const table = page.locator('table');
    await expect(table.getByRole('link', { name: 'Proyecto Web' })).toBeVisible();
    await expect(table.getByRole('link', { name: 'App Móvil' })).toBeVisible();
    await expect(table.getByText('Publicado')).toBeVisible();
    await expect(table.getByText('Borrador')).toBeVisible();
  });

  test('shows create button linking to /panel/portfolio/create', {
    tag: [...ADMIN_PORTFOLIO_LIST, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/portfolio');
    await page.waitForLoadState('networkidle');

    const createLink = page.getByRole('link', { name: /Nuevo Proyecto/ });
    await expect(createLink).toBeVisible();
    await expect(createLink).toHaveAttribute('href', '/panel/portfolio/create');
  });

  test('shows empty state when no works exist', {
    tag: [...ADMIN_PORTFOLIO_LIST, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, { works: [] });
    await page.goto('/panel/portfolio');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('No hay proyectos aún')).toBeVisible();
  });
});
