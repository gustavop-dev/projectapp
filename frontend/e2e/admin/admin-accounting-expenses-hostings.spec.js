/**
 * E2E tests for the accounting expenses and hostings subviews.
 *
 * FLOWS: admin-accounting-expenses-crud, admin-accounting-hostings
 * Covers: expense list + create + category badge; hosting list + meta
 *         stat cards + create + estado badge.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_EXPENSES_CRUD,
  ADMIN_ACCOUNTING_HOSTINGS,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const EXPENSE_ROW = {
  id: 1,
  concept: 'Claude Code 20x',
  period: '2026-03',
  period_label: 'Marzo 2026',
  period_date: '2026-03-01',
  category: 'business',
  category_label: 'Negocio',
  paid_from: 'partners',
  paid_from_label: 'Socios',
  total_amount: '400000.00',
  gustavo_amount: '200000.00',
  carlos_amount: '200000.00',
  company_amount: '0.00',
  pocket_movement: null,
  notes: '',
  created_at: '2026-03-01T10:00:00Z',
  updated_at: '2026-03-01T10:00:00Z',
};

const HOSTING_ROWS = [
  {
    id: 1,
    client_name: 'German - Kore',
    domain_url: 'https://korehealths.com/',
    monthly_value: '91667.00',
    payment_modality: 'semiannual',
    payment_modality_label: 'Semestral',
    benefit: '',
    valid_from: '2026-03-02',
    valid_to: '2026-09-02',
    cycles_count: 1,
    payment_per_cycle: '550002.00',
    total_paid: '1100000.00',
    is_active: true,
    notes: '',
    created_at: '2026-03-02T10:00:00Z',
    updated_at: '2026-03-02T10:00:00Z',
  },
  {
    id: 2,
    client_name: 'Nestor - Xpandia',
    domain_url: 'https://xpandia.global/',
    monthly_value: '19000.00',
    payment_modality: 'annual',
    payment_modality_label: 'Anual',
    benefit: '',
    valid_from: '2026-07-01',
    valid_to: '2027-07-01',
    cycles_count: 1,
    payment_per_cycle: '228000.00',
    total_paid: '228000.00',
    is_active: false,
    notes: '',
    created_at: '2026-07-01T10:00:00Z',
    updated_at: '2026-07-01T10:00:00Z',
  },
];

function buildHandler({ calls }) {
  return async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath === 'accounting/expenses/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [EXPENSE_ROW], meta: {} }),
      };
    }
    if (apiPath === 'accounting/expenses/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...EXPENSE_ROW, id: 99, ...body }),
      };
    }
    if (apiPath === 'accounting/hostings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: HOSTING_ROWS,
          meta: { active_count: 1, monthly_income: '91667.00' },
        }),
      };
    }
    if (apiPath === 'accounting/hostings/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...HOSTING_ROWS[0], id: 99, ...body }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

test.describe('Admin Accounting Expenses & Hostings', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('expenses list renders rows with the category badge', {
    tag: [...ADMIN_ACCOUNTING_EXPENSES_CRUD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/expenses', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Gastos' }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(page.getByText('Claude Code 20x')).toBeVisible();
    await expect(page.getByText('Negocio', { exact: true })).toBeVisible();
  });

  test('creates an expense through the modal', {
    tag: [...ADMIN_ACCOUNTING_EXPENSES_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/expenses', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Gastos' }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('expenses-new-button').click();
    await expect(page.getByRole('heading', { name: 'Nuevo gasto' })).toBeVisible();

    await page.locator('form input[type="text"]').first().fill('Windsurf Julio');
    await page.locator('form input[type="month"]').fill('2026-07');
    await page.getByTestId('partner-split-total').fill('3000000');
    await page.getByTestId('expense-form-submit').click();

    await expect(page.getByText('Gasto creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.concept).toBe('Windsurf Julio');
    expect(Number(calls[0].body.gustavo_amount)).toBe(1500000);
  });

  test('hostings list renders meta stat cards', {
    tag: [...ADMIN_ACCOUNTING_HOSTINGS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Hostings' }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByText('Hostings activos', { exact: true })).toBeVisible();
    await expect(page.getByText('Ingreso mensual', { exact: true })).toBeVisible();
    await expect(page.getByText('$91.667 COP').first()).toBeVisible();
  });

  test('hostings table shows domain and estado badge per row', {
    tag: [...ADMIN_ACCOUNTING_HOSTINGS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('accounting-row-1')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByText('German - Kore')).toBeVisible();
    await expect(page.getByText('Activo', { exact: true })).toBeVisible();
    await expect(page.getByText('Inactivo', { exact: true })).toBeVisible();
  });

  test('creates a hosting through the modal', {
    tag: [...ADMIN_ACCOUNTING_HOSTINGS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Hostings' }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('hostings-new-button').click();
    await expect(page.getByRole('heading', { name: 'Nuevo hosting' })).toBeVisible();

    await page.locator('form input[type="text"]').first().fill('Katerin Ruiz - Senses Candles');
    await page.locator('form input[type="number"]').first().fill('38333');
    await page.getByTestId('hosting-form-submit').click();

    await expect(page.getByText('Hosting creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.client_name).toBe('Katerin Ruiz - Senses Candles');
  });
});
