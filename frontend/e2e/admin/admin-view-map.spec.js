/**
 * E2E tests for the admin view-map reference page.
 *
 * Covers: page render, search filtering, reset behavior, and copy reference feedback.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_VIEW_MAP } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

test.describe('Admin View Map', () => {
  test.describe.configure({ mode: 'serial' });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8800, role: 'admin', is_staff: true },
    });
  });

  test('renders the view map with grouped route inventory', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText('Sitio publico')).toBeVisible();
    await expect(page.getByText('Panel administrativo')).toBeVisible();
    await expect(page.getByText('/panel/views', { exact: true })).toBeVisible();
  });

  test('search filters results and clearing search restores the catalog', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible({ timeout: 30_000 });

    const search = page.getByPlaceholder('Buscar vista por nombre, URL, referencia o archivo...');
    await search.fill('/panel/views');

    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 3 })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Inicio', level: 3 })).not.toBeVisible();

    await search.fill('');

    await expect(page.getByRole('heading', { name: 'Inicio', level: 3 })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 3 })).toBeVisible();
  });

  test('copy reference button shows copied feedback', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible({ timeout: 30_000 });

    const viewCard = page.locator('article').filter({ hasText: '/panel/views' }).first();
    const copyButton = viewCard.getByTitle('Copiar referencia');
    await copyButton.click();

    await expect(viewCard.getByTitle('Copiado!')).toBeVisible({ timeout: 5000 });
  });
});
