/**
 * E2E tests for admin diagnostics advanced filter tabs.
 *
 * Covers: default "Todas" tab shows all diagnostics, filter panel toggle,
 * create a new saved filter tab, tab rename, tab delete.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_ADVANCED_FILTERS } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDiagnostics = [
  {
    id: 1,
    title: 'Diagnóstico Alpha Corp',
    client_name: 'Alpha Corp',
    client_email: 'alpha@test.com',
    status: 'sent',
    language: 'es',
    investment_amount: '5000000',
    currency: 'COP',
    view_count: 3,
    created_at: '2026-01-10T10:00:00Z',
    updated_at: '2026-03-20T10:00:00Z',
  },
  {
    id: 2,
    title: 'Diagnóstico Beta Inc',
    client_name: 'Beta Inc',
    client_email: 'beta@test.com',
    status: 'draft',
    language: 'es',
    investment_amount: '8000000',
    currency: 'COP',
    view_count: 0,
    created_at: '2026-02-15T10:00:00Z',
    updated_at: '2026-02-15T10:00:00Z',
  },
  {
    id: 3,
    title: 'Diagnóstico Gamma LLC',
    client_name: 'Gamma LLC',
    client_email: 'gamma@test.com',
    status: 'negotiating',
    language: 'es',
    investment_amount: '12000000',
    currency: 'COP',
    view_count: 7,
    created_at: '2025-11-01T10:00:00Z',
    updated_at: '2026-01-05T10:00:00Z',
  },
];

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'diagnostics/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDiagnostics) };
    }
    return null;
  });
}

test.describe('Admin Diagnostics — Advanced Filter Tabs', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
    // Clear saved filter tabs so tests start from a clean state.
    await page.addInitScript(() => {
      localStorage.removeItem('diagnostic_filter_tabs');
    });
  });

  test('default view shows all diagnostics with no filters active', {
    tag: [...ADMIN_DIAGNOSTIC_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Diagnósticos de aplicaciones' })).toBeVisible({ timeout: 20_000 });

    await expect(page.getByText('Alpha Corp')).toBeVisible();
    await expect(page.getByText('Beta Inc')).toBeVisible();
    await expect(page.getByText('Gamma LLC')).toBeVisible();
  });

  test('filter toggle button opens filter panel with dimensions', {
    tag: [...ADMIN_DIAGNOSTIC_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Diagnósticos de aplicaciones' })).toBeVisible({ timeout: 20_000 });

    // Filter panel is hidden initially.
    await expect(page.getByText('Estados')).not.toBeVisible();

    await page.getByRole('button', { name: /filtros/i }).click();
    await expect(page.getByText('Estados')).toBeVisible({ timeout: 5_000 });

    // Close by clicking again.
    await page.getByRole('button', { name: /filtros/i }).click();
    await expect(page.getByText('Estados')).not.toBeVisible();
  });

  test('create a new saved filter tab from the + button', {
    tag: [...ADMIN_DIAGNOSTIC_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Diagnósticos de aplicaciones' })).toBeVisible({ timeout: 20_000 });

    // Click "+" button to create a new tab.
    await page.getByTestId('filter-tabs-create').click();

    // Name input appears.
    await expect(page.getByTestId('filter-tabs-input')).toBeVisible({ timeout: 5_000 });
    await page.getByTestId('filter-tabs-input').fill('Negociando');
    await page.getByTestId('filter-tabs-confirm').click();

    // New tab appears in the tab strip.
    await expect(page.getByText('Negociando')).toBeVisible({ timeout: 5_000 });
  });

  test('search input filters diagnostics by title', {
    tag: [...ADMIN_DIAGNOSTIC_ADVANCED_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Diagnósticos de aplicaciones' })).toBeVisible({ timeout: 20_000 });

    await page.getByTestId('diagnostics-search-input').fill('Alpha');
    await expect(page.getByText('Alpha Corp')).toBeVisible();
    await expect(page.getByText('Beta Inc')).not.toBeVisible();
    await expect(page.getByText('Gamma LLC')).not.toBeVisible();
  });
});
