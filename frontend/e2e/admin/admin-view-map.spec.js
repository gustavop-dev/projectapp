/**
 * E2E tests for the admin view-map reference page.
 *
 * Covers: page render, search filtering, reset behavior, copy reference feedback,
 * seeded filter tabs, configured default view mode, and the Configuración tab.
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

const seededTabs = [
  { id: 1, view: 'view_map', name: 'Admin', filters: { audiences: ['admin'] }, order: 0 },
  { id: 2, view: 'view_map', name: 'Público', filters: { audiences: ['public'] }, order: 1 },
  { id: 3, view: 'view_map', name: 'Cliente', filters: { audiences: ['client'] }, order: 2 },
  { id: 4, view: 'view_map', name: 'Dashboards', filters: { viewTypes: ['dashboard'] }, order: 3 },
  { id: 5, view: 'view_map', name: 'Configuración', filters: { viewTypes: ['config'] }, order: 4 },
];

function jsonResponse(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

function viewMapSettings(overrides = {}) {
  return jsonResponse({
    default_view_mode: 'list',
    default_filters: {},
    updated_at: '2026-07-16T10:00:00Z',
    ...overrides,
  });
}

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

  test('map mode drills down into a module and back', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('view-mode-map').click();
    await expect(page.getByTestId('view-module-grid')).toBeVisible();

    await page.getByTestId('view-module-card-admin-panel').click();
    await expect(page.getByTestId('view-module-detail')).toBeVisible();
    await expect(page).toHaveURL(/viewMode=map/);
    await expect(page).toHaveURL(/module=admin-panel/);
    await expect(page.getByRole('heading', { name: 'Blog', level: 3 })).toBeVisible();

    await page.getByTestId('view-module-back').click();
    await expect(page.getByTestId('view-module-grid')).toBeVisible();
    await expect(page).not.toHaveURL(/module=/);
  });

  test('direct link opens map mode with a module preselected', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });

    await page.goto('/panel/views?viewMode=map&module=client-platform', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('view-module-detail')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText('Plataforma de clientes').first()).toBeVisible();
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

    const viewCard = page.locator('article').filter({ hasText: '/panel/views' });
    const copyButton = viewCard.getByTitle('Copiar referencia');
    await copyButton.click();

    await expect(viewCard.getByTitle('Copiado!')).toBeVisible({ timeout: 5000 });
  });

  test('seeded filter tabs render and selecting Dashboards filters the catalog', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'accounts/saved-filter-tabs/') return jsonResponse(seededTabs);
      if (apiPath === 'view-map/admin/settings/') return viewMapSettings();
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible({ timeout: 30_000 });

    for (const tab of seededTabs) {
      await expect(page.getByTestId(`filter-tabs-tab-${tab.id}`)).toBeVisible();
    }

    await page.getByTestId('filter-tabs-tab-4').click();

    await expect(page.getByRole('heading', { name: 'Dashboard del panel', level: 3 })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 3 })).not.toBeVisible();
  });

  test('configured default view mode opens the page in map mode', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'view-map/admin/settings/') return viewMapSettings({ default_view_mode: 'map' });
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('view-module-grid')).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveURL(/viewMode=map/);
  });

  test('?viewMode=list wins over the configured map default', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'view-map/admin/settings/') return viewMapSettings({ default_view_mode: 'map' });
      return null;
    });

    await page.goto('/panel/views?viewMode=list', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Inicio', level: 3 })).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('view-module-grid')).not.toBeVisible();
  });

  test('config tab saves the default view mode and shows a toast', {
    tag: [...ADMIN_VIEW_MAP, '@role:admin'],
  }, async ({ page }) => {
    let patchBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'view-map/admin/settings/') return viewMapSettings();
      if (apiPath === 'view-map/admin/settings/update/' && method === 'PATCH') {
        patchBody = route.request().postDataJSON();
        return viewMapSettings({ default_view_mode: 'map' });
      }
      return null;
    });

    await page.goto('/panel/views', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('view-map-section-config').click();
    await expect(page.getByText('Vista por defecto')).toBeVisible();
    await expect(page.getByText('Filtros por defecto')).toBeVisible();

    await page.getByTestId('view-map-default-mode').getByTestId('view-mode-map').click();

    await expect(page.getByText('Vista por defecto guardada.')).toBeVisible({ timeout: 5000 });
    expect(patchBody).toEqual({ default_view_mode: 'map' });
  });
});
