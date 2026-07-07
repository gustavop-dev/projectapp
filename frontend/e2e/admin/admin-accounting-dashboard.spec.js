/**
 * E2E tests for the accounting dashboard (superuser-only module).
 *
 * FLOW: admin-accounting-dashboard
 * Covers: stat cards from the summary endpoint, monthly table, subnav
 *         navigation, sidebar visibility for superusers and the gating
 *         redirect for staff non-superusers.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_DASHBOARD } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const MONTHS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const DASHBOARD_SUMMARY = {
  year: 2026,
  expected_total: '95238699.00',
  liquid_total: '59516261.00',
  difference: '-35722438.00',
  expenses_total: '62628212.00',
  expected_utility: '32610487.00',
  liquid_utility: '-3111951.00',
  pocket_balance: '1147378.00',
  partners: {
    gustavo: { expected: '54846399.00', liquid: '37040740.00', expenses: '36771980.00', net: '268760.00' },
    carlos: { expected: '40392300.00', liquid: '22475521.00', expenses: '13452275.00', net: '9023246.00' },
    company: { expected: '0.00', liquid: '0.00', expenses: '12403957.00', net: '0.00' },
  },
  monthly: MONTHS.map((label, index) => ({
    period: `2026-${String(index + 1).padStart(2, '0')}`,
    label: `${label} 2026`,
    expected: index === 1 ? '1160000.00' : '0.00',
    liquid: index === 1 ? '900000.00' : '0.00',
    expenses: index === 2 ? '400000.00' : '0.00',
    expected_utility: '0.00',
    utility: '0.00',
  })),
  recurring_monthly_cost: '3016059.00',
  ads: { year_total: '1008404.00', current_month_total: '0.00' },
  hostings: { active_count: 6, monthly_income: '288356.00', total_paid: '4574080.00' },
  latest_card_snapshots: [
    {
      card_name: 'T.C 0064',
      snapshot_date: '2026-07-01',
      available_amount: '3849046.00',
      debt_amount: '4150954.00',
    },
  ],
};

function buildHandler({ isSuperuser = true } = {}) {
  return ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: isSuperuser },
        }),
      };
    }
    if (apiPath.startsWith('accounting/dashboard/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(DASHBOARD_SUMMARY),
      };
    }
    if (apiPath.startsWith('accounting/incomes/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], meta: {} }),
      };
    }
    if (apiPath.startsWith('accounting/card-snapshots/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: 1, card_name: 'T.C 0064', snapshot_date: '2026-06-17',
              available_amount: '413226.00', debt_amount: '7586774.00', notes: '',
            },
            {
              id: 2, card_name: 'T.C 0064', snapshot_date: '2026-07-01',
              available_amount: '3849046.00', debt_amount: '4150954.00', notes: '',
            },
          ],
          meta: {},
        }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

test.describe('Admin Accounting Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('renders stat cards with the summary totals', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Resumen', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('accounting-hero-kpi')).toBeVisible();
    await expect(page.getByTestId('accounting-hero-value')).toBeVisible();
    await expect(page.getByText('Ingresos esperados')).toBeVisible();
    await expect(page.getByText('$95.238.699 COP')).toBeVisible();
    await expect(page.getByText('$59.516.261 COP')).toBeVisible();
    await expect(page.getByText('Bolsillo ProjectApp')).toBeVisible();
    await expect(page.getByText('$1.147.378 COP').first()).toBeVisible();
  });

  test('renders the 12-month breakdown with a totals row', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Detalle mensual 2026')).toBeVisible({ timeout: 25_000 });
    // Month labels also appear inside the charts' SVG: assert on the cells.
    await expect(page.getByRole('cell', { name: 'Enero 2026' })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Diciembre 2026' })).toBeVisible();
    await expect(
      page.getByRole('cell', { name: 'Total', exact: true }),
    ).toBeVisible();
  });

  test('renders the evolution charts and reacts to the month range', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Evolución 2026')).toBeVisible({ timeout: 25_000 });
    const monthlyChart = page.getByTestId('accounting-monthly-chart');
    await expect(monthlyChart.locator('.apexcharts-canvas')).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByTestId('accounting-card-debt-chart').locator('.apexcharts-canvas'),
    ).toBeVisible();

    // Narrow the range to a window without movements: empty state appears.
    await page.getByTestId('accounting-month-from').selectOption('7');
    await page.getByTestId('accounting-month-to').selectOption('8');
    await expect(monthlyChart.getByText('Sin movimientos en el rango')).toBeVisible();
  });

  test('links to the cards history from the Tarjetas table', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('accounting-cards-link')).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('accounting-cards-link').click();
    await expect(page).toHaveURL(/\/panel\/accounting\/cards/);
  });

  test('subnav pill navigates to the incomes subview', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Resumen', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('accounting-subnav-incomes').click();

    await expect(page).toHaveURL(/\/panel\/accounting\/incomes/);
    await expect(page.getByRole('heading', { name: 'Ingresos', exact: true })).toBeVisible();
  });

  test('sidebar shows the Accounting section for superusers', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Resumen', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(
      page
        .getByRole('navigation', { name: 'Navegación del panel' })
        .getByRole('link', { name: 'Ingresos' }),
    ).toBeVisible();
  });

  test('staff non-superuser is redirected to /panel and sees no Accounting section', {
    tag: [...ADMIN_ACCOUNTING_DASHBOARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ isSuperuser: false }));
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    await expect(page).toHaveURL(/\/panel\/?$/, { timeout: 25_000 });
    await expect(
      page
        .getByRole('navigation', { name: 'Navegación del panel' })
        .getByRole('link', { name: 'Ingresos' }),
    ).toHaveCount(0);
  });
});
