/**
 * E2E test for the accounting list load-error + retry flow.
 *
 * FLOW: admin-accounting-list-error-retry
 * A failed GET /api/accounting/incomes/ replaces the table with
 * AccountingErrorState (data-testid=accounting-error-retry); the Reintentar
 * button re-fires the page load and, once the API recovers, restores the table.
 * Exercised on the incomes subview as a representative accounting list.
 * Mirrors admin-diagnostic-list-error-retry.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_LIST_ERROR_RETRY } from '../helpers/flow-tags.js';

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

test.describe('Admin Accounting List — load error & retry', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('shows the error state on a failed load and recovers on retry', {
    tag: [...ADMIN_ACCOUNTING_LIST_ERROR_RETRY, '@role:admin'],
  }, async ({ page }) => {
    let listCalls = 0;

    await mockApi(page, async ({ apiPath, method }) => {
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
        listCalls += 1;
        if (listCalls === 1) {
          return {
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'boom' }),
          };
        }
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ results: [incomeRow()], meta: {} }),
        };
      }
      if (apiPath.startsWith('accounts/saved-filter-tabs')) {
        return { status: 200, contentType: 'application/json', body: '[]' };
      }
      return null;
    });

    await page.goto('/panel/accounting/incomes', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Ingresos', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    // Failed first load surfaces the list-level error state (not a toast).
    const retry = page.getByTestId('accounting-error-retry');
    await expect(retry).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText('No se pudieron cargar los ingresos')).toBeVisible();

    // Retrying re-fires the load; on recovery the table replaces the error state.
    await retry.click();

    await expect(page.getByText('Kore - Inicio 40%')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId('accounting-error-retry')).toBeHidden();
    expect(listCalls).toBeGreaterThanOrEqual(2);
  });
});
