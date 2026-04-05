/**
 * E2E tests for admin proposal advanced filters & saved tabs.
 *
 * @flow:admin-proposal-advanced-filters
 * Covers: filter panel toggle, status filter, tab creation, tab persistence, tab rename, tab delete, filter reset.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_ADVANCED_FILTERS } from '../helpers/flow-tags.js';

const mockProposals = [
  {
    id: 1, uuid: 'aaa-111', title: 'Proyecto Web', client_name: 'Cliente A', client_email: 'a@e2e.com',
    status: 'draft', language: 'es', total_investment: '5000000', currency: 'COP', project_type: 'web_design',
    market_type: 'b2b', view_count: 0, heat_score: 3, sent_at: null, is_active: true,
    created_at: '2026-01-01T12:00:00Z', last_activity_at: '2026-01-02T12:00:00Z',
    engagement_summary: { technical_viewed: false },
  },
  {
    id: 2, uuid: 'bbb-222', title: 'App Móvil', client_name: 'Cliente B', client_email: 'b@e2e.com',
    status: 'sent', language: 'en', total_investment: '15000000', currency: 'USD', project_type: 'mobile_app',
    market_type: 'b2c', view_count: 5, heat_score: 8, sent_at: '2026-01-03T12:00:00Z', is_active: true,
    created_at: '2026-01-02T12:00:00Z', last_activity_at: '2026-01-05T12:00:00Z',
    engagement_summary: { technical_viewed: true },
  },
  {
    id: 3, uuid: 'ccc-333', title: 'Plataforma SaaS', client_name: 'Cliente C', client_email: 'c@e2e.com',
    status: 'viewed', language: 'es', total_investment: '30000000', currency: 'COP', project_type: 'software',
    market_type: 'b2b', view_count: 12, heat_score: 6, sent_at: '2026-01-04T12:00:00Z', is_active: false,
    created_at: '2026-01-03T12:00:00Z', last_activity_at: '2026-01-06T12:00:00Z',
    engagement_summary: { technical_viewed: false },
  },
];

const TAB_SEED = {
  statuses: [], projectTypes: [], marketTypes: [], currencies: [], languages: [],
  investmentMin: null, investmentMax: null, heatScoreMin: null, heatScoreMax: null,
  viewCountMin: null, viewCountMax: null, createdAfter: null, createdBefore: null,
  lastActivityAfter: null, lastActivityBefore: null, isActive: 'all',
};

function buildMockHandler(proposals = mockProposals) {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === 'proposals/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposals) };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: proposals.length, conversion_rate: 0 }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  };
}

function seedTabs(page, tabs) {
  return page.addInitScript((tabsJson) => {
    localStorage.setItem('proposal_filter_tabs', tabsJson);
  }, JSON.stringify(tabs));
}

test.describe('Admin Proposal Advanced Filters & Saved Tabs', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
    await page.addInitScript(() => localStorage.removeItem('proposal_filter_tabs'));
  });

  test('shows Filtros button and toggles filter panel', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    // Wait for Vue to mount — dynamic proposal data proves the app is active
    await expect(page.getByText('Cliente A')).toBeVisible({ timeout: 20_000 });

    const filtrosBtn = page.getByRole('button', { name: /Filtros/ });
    await expect(filtrosBtn).toBeVisible();

    // "Borrador" pill only exists inside the filter panel
    const borradorPill = page.getByRole('button', { name: 'Borrador' });
    await expect(borradorPill).not.toBeVisible();

    // Click to open
    await filtrosBtn.click();
    await expect(borradorPill).toBeVisible({ timeout: 5_000 });

    // Click to close
    await filtrosBtn.click();
    await expect(borradorPill).not.toBeVisible();
  });

  test('filters proposals by status pill', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    // Open filter panel
    await page.getByRole('button', { name: /Filtros/ }).click();

    // All 3 proposals visible in table
    await expect(page.getByText('Cliente A')).toBeVisible();
    await expect(page.getByText('Cliente B')).toBeVisible();
    await expect(page.getByText('Cliente C')).toBeVisible();

    // Click "Borrador" status pill
    await page.getByRole('button', { name: 'Borrador' }).click();

    // Only draft proposal remains
    await expect(page.getByText('Cliente A')).toBeVisible();
    await expect(page.getByText('Cliente B')).not.toBeVisible();
    await expect(page.getByText('Cliente C')).not.toBeVisible();

    // Filter badge shows "1"
    await expect(page.getByRole('button', { name: /Filtros/ }).locator('span')).toContainText('1');
  });

  test('creates a new saved tab from current filters', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    // Open filters and select a status
    await page.getByRole('button', { name: /Filtros/ }).click();
    await page.getByRole('button', { name: 'Borrador' }).click();

    // Click "+" button in the tab bar (svg with plus path)
    const addTabBtn = page.locator('.hidden.md\\:flex').locator('button:has(svg)').last();
    await addTabBtn.click();

    // Type tab name and save
    const nameInput = page.getByPlaceholder('Nombre de la pestaña...');
    await expect(nameInput).toBeVisible();
    await nameInput.fill('Mis Borradores');
    await page.getByRole('button', { name: 'Guardar' }).click();

    // Tab visible in tab bar
    await expect(page.getByRole('button', { name: 'Mis Borradores' })).toBeVisible();

    // URL has tab query param
    await expect(page).toHaveURL(/tab=/);
  });

  test('Todas tab resets all filters', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    // Apply a filter
    await page.getByRole('button', { name: /Filtros/ }).click();
    await page.getByRole('button', { name: 'Borrador' }).click();
    await expect(page.getByText('Cliente B')).not.toBeVisible();

    // Click "Todas" tab
    await page.getByRole('button', { name: 'Todas' }).click();

    // All proposals visible again
    await expect(page.getByText('Cliente A')).toBeVisible();
    await expect(page.getByText('Cliente B')).toBeVisible();
    await expect(page.getByText('Cliente C')).toBeVisible();
  });

  test('clears filters with Limpiar filtros button', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });

    // Apply a filter
    await page.getByRole('button', { name: /Filtros/ }).click();
    await page.getByRole('button', { name: 'Borrador' }).click();

    // Click clear
    await page.getByRole('button', { name: /Limpiar filtros/ }).click();

    // All proposals visible
    await expect(page.getByText('Cliente A')).toBeVisible();
    await expect(page.getByText('Cliente B')).toBeVisible();
    await expect(page.getByText('Cliente C')).toBeVisible();
  });

  test('saved tab persists after page reload', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());

    // Seed a tab (runs after beforeEach clear, so tab will persist)
    await seedTabs(page, [{
      id: 'test-tab-1', name: 'Tab Persistente',
      filters: { ...TAB_SEED, statuses: ['sent'] },
      createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z',
    }]);

    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    // Tab visible
    await expect(page.getByRole('button', { name: 'Tab Persistente' })).toBeVisible({ timeout: 20_000 });

    // Click the saved tab �� filters apply
    await page.getByRole('button', { name: 'Tab Persistente' }).click();

    // Only sent proposals show
    await expect(page.getByText('Cliente B')).toBeVisible();
    await expect(page.getByText('Cliente A')).not.toBeVisible();
  });

  test('renames a saved tab via context menu', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await seedTabs(page, [{
      id: 'rename-tab', name: 'Nombre Viejo', filters: TAB_SEED,
      createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z',
    }]);

    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('button', { name: 'Nombre Viejo' })).toBeVisible({ timeout: 20_000 });

    // Hover the tab group to reveal 3-dot menu
    const tabGroup = page.locator('.group').filter({ hasText: 'Nombre Viejo' });
    await tabGroup.hover();
    await tabGroup.locator('button').nth(1).click();

    // Click "Renombrar" in dropdown
    await page.getByRole('button', { name: 'Renombrar' }).click();

    // Fill new name
    const nameInput = page.getByPlaceholder('Nuevo nombre...');
    await expect(nameInput).toBeVisible();
    await nameInput.clear();
    await nameInput.fill('Nombre Nuevo');
    await page.getByRole('button', { name: 'Renombrar' }).click();

    // Renamed tab visible
    await expect(page.getByRole('button', { name: 'Nombre Nuevo' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Nombre Viejo' })).not.toBeVisible();
  });

  test('deletes a saved tab via context menu', {
    tag: [...ADMIN_PROPOSAL_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await seedTabs(page, [{
      id: 'delete-tab', name: 'Tab a Eliminar', filters: TAB_SEED,
      createdAt: '2026-01-01T00:00:00Z', updatedAt: '2026-01-01T00:00:00Z',
    }]);

    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('button', { name: 'Tab a Eliminar' })).toBeVisible({ timeout: 20_000 });

    // Hover tab group → click 3-dot menu
    const tabGroup = page.locator('.group').filter({ hasText: 'Tab a Eliminar' });
    await tabGroup.hover();
    await tabGroup.locator('button').nth(1).click();

    // Click "Eliminar"
    await page.getByRole('button', { name: 'Eliminar' }).click();

    // Tab removed
    await expect(page.getByRole('button', { name: 'Tab a Eliminar' })).not.toBeVisible();
  });
});
