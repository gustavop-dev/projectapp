/**
 * E2E tests for accounting list empty states and their CTAs.
 *
 * FLOW: admin-accounting-empty-state-cta
 * Covers: the zero-records empty state with a primary 'Nuevo <entidad>' CTA that
 *         opens the create modal, and the filtered-no-match variant whose CTA
 *         becomes 'Limpiar filtros' and resets the filter panel. Exercised on the
 *         incomes subview as a representative accounting list.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_EMPTY_STATE_CTA } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function incomeRow(overrides = {}) {
  return {
    id: 1,
    concept: 'Kore - Inicio 40%',
    kind: 'expected',
    kind_label: 'Esperado',
    period: '2026-02',
    period_label: 'Febrero 2026',
    period_date: '2026-02-01',
    destination: 'partners',
    destination_label: 'Socios',
    ledger: 'company',
    ledger_label: 'Empresa',
    total_amount: '1160000.00',
    gustavo_amount: '580000.00',
    carlos_amount: '580000.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    notes: '',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
    ...overrides,
  };
}

function buildHandler({ rows }) {
  return async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath === 'accounting/incomes/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: rows, meta: {} }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function gotoIncomes(page) {
  await page.goto('/panel/accounting/incomes', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Ingresos', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
}

test.describe('Admin Accounting Empty State CTA', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('zero records shows the create CTA that opens the modal', {
    tag: [...ADMIN_ACCOUNTING_EMPTY_STATE_CTA, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ rows: [] }));
    await gotoIncomes(page);

    await expect(page.getByText('No hay ingresos aún')).toBeVisible();

    // The empty-state CTA is the last 'Nuevo ingreso' button (the header also has one).
    const cta = page.getByRole('button', { name: 'Nuevo ingreso' }).last();
    await expect(cta).toBeVisible();
    await cta.click();

    await expect(page.getByRole('heading', { name: 'Nuevo ingreso' })).toBeVisible();
  });

  test('filtered-with-no-match swaps the CTA for Limpiar filtros and resets', {
    tag: [...ADMIN_ACCOUNTING_EMPTY_STATE_CTA, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ rows: [incomeRow()] }));
    await gotoIncomes(page);

    // Row is present before filtering.
    await expect(page.getByText('Kore - Inicio 40%')).toBeVisible();

    // A search matching nothing collapses the list to the filtered empty state.
    await page.getByTestId('incomes-search-input').fill('zzz-no-match-zzz');
    await expect(page.getByText('Sin resultados con esos filtros')).toBeVisible();

    // The empty-state CTA is the last 'Limpiar filtros' button (the filter panel
    // has its own reset control, data-testid=accounting-filter-reset).
    const reset = page.getByRole('button', { name: 'Limpiar filtros' }).last();
    await expect(reset).toBeVisible();
    await reset.click();

    // Clearing filters restores the row.
    await expect(page.getByText('Kore - Inicio 40%')).toBeVisible();
  });
});
