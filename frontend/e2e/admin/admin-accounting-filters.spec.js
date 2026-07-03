/**
 * E2E tests for the accounting incomes filters.
 *
 * FLOW: admin-accounting-filters
 * Covers: date range, amount range, partner segmented filter, active
 *         filter count badge, reset and free-text search.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_FILTERS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const ROWS = [
  {
    id: 1,
    concept: 'Kore - Inicio 40%',
    kind: 'expected',
    kind_label: 'Esperado',
    period: '2026-02',
    period_label: 'Febrero 2026',
    period_date: '2026-02-01',
    destination: 'partners',
    destination_label: 'Socios',
    total_amount: '1160000.00',
    gustavo_amount: '580000.00',
    carlos_amount: '580000.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    notes: '',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
  },
  {
    id: 2,
    concept: 'G&M Entrega No. 1 (Mayo)',
    kind: 'expected',
    kind_label: 'Esperado',
    period: '2026-05',
    period_label: 'Mayo 2026',
    period_date: '2026-05-01',
    destination: 'partners',
    destination_label: 'Socios',
    total_amount: '3553750.00',
    gustavo_amount: '1776875.00',
    carlos_amount: '1776875.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    notes: '',
    created_at: '2026-05-01T10:00:00Z',
    updated_at: '2026-05-01T10:00:00Z',
  },
  {
    id: 3,
    concept: 'Vastago (Fase 1) - Inicio 40%',
    kind: 'liquid',
    kind_label: 'Líquido',
    period: '2026-04',
    period_label: 'Abril 2026',
    period_date: '2026-04-01',
    destination: 'pocket',
    destination_label: 'Bolsillo ProjectApp',
    total_amount: '2123000.00',
    gustavo_amount: '0.00',
    carlos_amount: '0.00',
    company_amount: '2123000.00',
    expected_income: null,
    pocket_movement: 7,
    notes: '',
    created_at: '2026-04-29T10:00:00Z',
    updated_at: '2026-04-29T10:00:00Z',
  },
  {
    id: 4,
    concept: 'Universidad Nacional',
    kind: 'liquid',
    kind_label: 'Líquido',
    period: '2026-02',
    period_label: 'Febrero 2026',
    period_date: '2026-02-01',
    destination: 'partners',
    destination_label: 'Socios',
    total_amount: '1400000.00',
    gustavo_amount: '1400000.00',
    carlos_amount: '0.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    notes: '',
    created_at: '2026-02-10T10:00:00Z',
    updated_at: '2026-02-10T10:00:00Z',
  },
];

function buildHandler() {
  return ({ apiPath, method }) => {
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
        body: JSON.stringify({ results: ROWS, meta: {} }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function gotoIncomes(page) {
  await mockApi(page, buildHandler());
  await page.goto('/panel/accounting/incomes', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Ingresos' }),
  ).toBeVisible({ timeout: 25_000 });
  await expect(page.getByTestId('accounting-row-1')).toBeVisible();
}

function visibleRows(page) {
  return page.locator('[data-testid^="accounting-row-"]');
}

async function openFilterPanel(page) {
  await page.getByRole('button', { name: /Filtros/ }).click();
}

test.describe('Admin Accounting Filters', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('date range keeps only rows inside the period', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('button', { name: /^Mes/ }).click();
    const dateInputs = page.locator('input[type="date"]');
    await dateInputs.first().fill('2026-04-01');
    await dateInputs.nth(1).fill('2026-05-31');

    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByText('G&M Entrega No. 1 (Mayo)')).toBeVisible();
    await expect(page.getByText('Kore - Inicio 40%')).toHaveCount(0);
  });

  test('amount range filters by total', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('button', { name: /^Total/ }).click();
    const numberInputs = page.locator('input[type="number"]');
    await numberInputs.first().fill('2000000');
    await numberInputs.nth(1).fill('4000000');

    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();
    await expect(page.getByText('Universidad Nacional')).toHaveCount(0);
  });

  test('partner segmented filter distinguishes Gustavo from ProjectApp', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Gustavo', exact: true }).click();
    await expect(visibleRows(page)).toHaveCount(3);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toHaveCount(0);

    await page.getByRole('tab', { name: 'ProjectApp' }).click();
    await expect(visibleRows(page)).toHaveCount(1);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();
  });

  test('active filter count badge reflects applied filters', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Líquido' }).click();
    await page.getByRole('tab', { name: 'Gustavo', exact: true }).click();

    await expect(page.getByRole('button', { name: /Filtros/ })).toContainText('2');
  });

  test('reset restores the full list', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Líquido' }).click();
    await expect(visibleRows(page)).toHaveCount(2);

    await page.getByTestId('accounting-filter-reset').click();
    await expect(visibleRows(page)).toHaveCount(4);
  });

  test('free search filters by concept', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin'],
  }, async ({ page }) => {
    await gotoIncomes(page);

    await page.getByTestId('incomes-search-input').fill('vastago');
    await expect(visibleRows(page)).toHaveCount(1, { timeout: 10_000 });
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();
  });
});
