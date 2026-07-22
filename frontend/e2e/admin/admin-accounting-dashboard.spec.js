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
import {
  ADMIN_ACCOUNTING_DASHBOARD,
  ADMIN_ACCOUNTING_EXPECTED_DETAIL,
  ADMIN_ACCOUNTING_STATS_MODALS,
} from '../helpers/flow-tags.js';

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
  expected_current_month: { period: '2026-07', label: 'Julio 2026', total: '2500000.00' },
  card_debt: {
    total: '4150954.00',
    card_count: 1,
    credit_limit_total: '8000000.00',
    utilization_pct: 51.9,
  },
};

const EXPECTED_MONTH_ROWS = [
  {
    id: 71,
    concept: 'Kore v2 (Fase 1) - Inicio 40%',
    period_label: 'Julio 2026',
    total_amount: '2000000.00',
    paid_amount: '500000.00',
    pending_amount: '1500000.00',
    payment_status: 'partial',
    payment_status_label: 'Parcial',
  },
  {
    id: 72,
    concept: 'Hosting anual Acme',
    period_label: '17 Julio 2026',
    total_amount: '1000000.00',
    paid_amount: '0.00',
    pending_amount: '1000000.00',
    payment_status: 'pending',
    payment_status_label: 'Pendiente',
  },
];

const STATS_PAYLOAD = {
  year: 2026,
  income: {
    liquid: {
      count: 12, total: '59516261.00', avg: '4959688.42',
      min: '288356.00', max: '9000000.00',
    },
    expected: {
      count: 15, total: '95238699.00', avg: '6349246.60',
      min: '500000.00', max: '12000000.00',
    },
    lost_total: '1200000.00',
    top_concepts: [
      { concept: 'Kore v2 (Fase 1)', total: '18000000.00', count: 3 },
      { concept: 'Hosting anual Acme', total: '9000000.00', count: 2 },
    ],
  },
  expenses: {
    summary: {
      count: 40, total: '62628212.00', avg: '1565705.30',
      min: '25000.00', max: '8000000.00',
    },
    by_category: [
      { category: 'business', label: 'Negocio', total: '50000000.00', count: 30 },
      { category: 'personal', label: 'Personal', total: '12628212.00', count: 10 },
    ],
    top_concepts: [
      { concept: 'Claude Code 20x', total: '9600000.00', count: 12 },
    ],
    recurring_monthly_cost: '3016059.00',
  },
};

function buildHandler({ isSuperuser = true } = {}) {
  return ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: isSuperuser },
        }),
      };
    }
    if (apiPath.startsWith('accounting/stats/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(STATS_PAYLOAD),
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
      const url = route.request().url();
      if (url.includes('kind=expected') && url.includes('date_from=2026-07-01')) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ results: EXPECTED_MONTH_ROWS, meta: {} }),
        };
      }
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
    await expect(page.getByTestId('accounting-hero-utility-chart')).toBeVisible();
    const expectedMonth = page.getByTestId('accounting-card-expected-month');
    await expect(expectedMonth).toContainText('Pendiente por cobrar · Julio 2026');
    await expect(expectedMonth).toContainText('$2.500.000 COP');

    const cardDebt = page.getByTestId('accounting-card-debt');
    await expect(cardDebt).toContainText('Deuda tarjetas');
    await expect(cardDebt).toContainText('$4.150.954 COP');
    await expect(cardDebt).toContainText('1 tarjeta · 51.9% del cupo');

    await expect(page.getByText('Ingresos líquidos')).toBeVisible();
    await expect(page.getByText('$59.516.261 COP')).toBeVisible();
    await expect(page.getByText('Bolsillo ProjectApp')).toBeVisible();
    await expect(page.getByText('$1.147.378 COP').first()).toBeVisible();
  });

  test('expected-month card opens the read-only detail modal', {
    tag: [...ADMIN_ACCOUNTING_EXPECTED_DETAIL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    const card = page.getByTestId('accounting-card-expected-month');
    await expect(card).toBeVisible({ timeout: 25_000 });
    await card.click();

    await expect(page.getByTestId('expected-income-detail-modal')).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Pendiente por cobrar — Julio 2026' }),
    ).toBeVisible();
    const rows = page.getByTestId('expected-income-row');
    await expect(rows).toHaveCount(2);
    await expect(rows.first()).toContainText('Kore v2 (Fase 1) - Inicio 40%');
    await expect(rows.first()).toContainText('Parcial');
    // Per-row clamped pending amounts sum to the card total.
    await expect(page.getByTestId('expected-income-pending-sum')).toContainText('$2.500.000 COP');

    await page.getByRole('button', { name: 'Cerrar' }).click();
    await expect(page.getByTestId('expected-income-detail-modal')).toHaveCount(0);
  });

  test('liquid-income card opens the stats modal with tabbed charts', {
    tag: [...ADMIN_ACCOUNTING_STATS_MODALS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler());
    await page.goto('/panel/accounting', { waitUntil: 'domcontentloaded' });

    const card = page.getByTestId('accounting-card-liquid-income');
    await expect(card).toBeVisible({ timeout: 25_000 });
    await card.click();

    await expect(page.getByTestId('stats-modal')).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Estadísticas de ingresos 2026' }),
    ).toBeVisible();
    await expect(
      page.getByTestId('stats-line-chart').locator('.apexcharts-canvas'),
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole('tab', { name: 'Top conceptos' }).click();
    await expect(page.getByText('Ticket promedio')).toBeVisible();
    await expect(page.getByText('Kore v2 (Fase 1)').first()).toBeVisible();
    await expect(
      page.getByTestId('stats-bar-chart').locator('.apexcharts-canvas'),
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole('button', { name: 'Cerrar' }).click();
    await expect(page.getByTestId('stats-modal')).toHaveCount(0);
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
