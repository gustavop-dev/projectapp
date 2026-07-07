/**
 * E2E tests for the accounting incomes subview.
 *
 * FLOW: admin-accounting-income-crud
 * Covers: list rendering, create via modal with automatic 50/50 partner
 *         split, HTML5 validation, edit prefill, delete with confirmation
 *         (confirm and cancel) and API-error surfacing.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_INCOME_CRUD } from '../helpers/flow-tags.js';

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

function buildHandler({ rows, calls, createStatus = 201 }) {
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
    if (apiPath === 'accounting/incomes/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: rows, meta: {} }),
      };
    }
    if (apiPath === 'accounting/incomes/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ method, apiPath, body });
      if (createStatus !== 201) {
        return {
          status: createStatus,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Monto inválido', code: 'invalid_amount' }),
        };
      }
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(incomeRow({ id: 99, ...body })),
      };
    }
    if (/^accounting\/incomes\/\d+\/update\/$/.test(apiPath) && method === 'PATCH') {
      const body = route.request().postDataJSON();
      calls.push({ method, apiPath, body });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(incomeRow({ ...rows[0], ...body })),
      };
    }
    if (/^accounting\/incomes\/\d+\/delete\/$/.test(apiPath) && method === 'DELETE') {
      calls.push({ method, apiPath });
      return { status: 204, contentType: 'application/json', body: '' };
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

test.describe('Admin Accounting Incomes CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('renders the mocked income rows', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({
      rows: [incomeRow(), incomeRow({ id: 2, concept: 'Tendalux - Inicio 40%' })],
      calls,
    }));
    await gotoIncomes(page);

    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(page.getByTestId('accounting-row-2')).toBeVisible();
    await expect(page.getByText('Kore - Inicio 40%')).toBeVisible();
  });

  test('creates an income with automatic 50/50 split', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [], calls }));
    await gotoIncomes(page);

    await page.getByTestId('incomes-new-button').click();
    await expect(page.getByRole('heading', { name: 'Nuevo ingreso' })).toBeVisible();

    await page.locator('form input[type="text"]').first().fill('Vastago (Fase 1) - Inicio 40%');
    await page.locator('form input[type="month"]').fill('2026-04');
    await page.getByTestId('partner-split-total').fill('2123000');
    await page.getByTestId('income-form-submit').click();

    await expect(page.getByText('Ingreso creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.concept).toBe('Vastago (Fase 1) - Inicio 40%');
    expect(Number(calls[0].body.gustavo_amount)).toBe(1061500);
    expect(Number(calls[0].body.carlos_amount)).toBe(1061500);
  });

  test('creates a personal-ledger income with a single value field', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [], calls }));
    await gotoIncomes(page);

    await page.getByTestId('incomes-new-button').click();
    await expect(page.getByRole('heading', { name: 'Nuevo ingreso' })).toBeVisible();

    await page.locator('form input[type="text"]').first().fill('Universidad Nacional');
    await page.locator('form input[type="month"]').fill('2026-02');
    await page.getByRole('tab', { name: 'Personal Gustavo' }).click();

    // Personal ledger swaps the partner split for a single value input.
    await expect(page.getByTestId('partner-split-total')).toHaveCount(0);
    await page.locator('form input[type="number"]').fill('1400000');
    await page.getByTestId('income-form-submit').click();

    await expect(page.getByText('Ingreso creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.ledger).toBe('gustavo');
    expect(Number(calls[0].body.total_amount)).toBe(1400000);
    expect(calls[0].body.gustavo_amount).toBeUndefined();
    expect(calls[0].body.carlos_amount).toBeUndefined();
  });

  test('empty required fields block the POST via HTML5 validation', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [], calls }));
    await gotoIncomes(page);

    await page.getByTestId('incomes-new-button').click();
    await page.getByTestId('income-form-submit').click();

    // The native required validation keeps the form open and fires no POST.
    await expect(page.getByRole('heading', { name: 'Nuevo ingreso' })).toBeVisible();
    expect(calls).toHaveLength(0);
  });

  test('edit prefills the record and PATCHes the change', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    const rows = [incomeRow()];
    await mockApi(page, buildHandler({ rows, calls }));
    await gotoIncomes(page);

    await page.getByTestId('accounting-edit-1').click();
    await expect(page.getByRole('heading', { name: 'Editar ingreso' })).toBeVisible();
    await expect(page.locator('form input[type="text"]').first()).toHaveValue('Kore - Inicio 40%');

    await page.getByTestId('partner-split-total').fill('2000000');
    await page.getByTestId('income-form-submit').click();

    await expect(page.getByText('Ingreso actualizado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].method).toBe('PATCH');
    expect(Number(calls[0].body.total_amount)).toBe(2000000);
  });

  test('delete asks for confirmation and removes the row', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [incomeRow()], calls }));
    await gotoIncomes(page);

    await page.getByTestId('accounting-delete-1').click();
    await expect(page.getByText('Eliminar ingreso')).toBeVisible();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Ingreso eliminado')).toBeVisible();
    await expect(page.getByTestId('accounting-row-1')).toHaveCount(0);
    expect(calls.some((call) => call.method === 'DELETE')).toBe(true);
  });

  test('cancelling the confirmation fires no DELETE', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [incomeRow()], calls }));
    await gotoIncomes(page);

    await page.getByTestId('accounting-delete-1').click();
    await expect(page.getByText('Eliminar ingreso')).toBeVisible();
    await page.getByRole('button', { name: 'Cancelar' }).click();

    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    expect(calls.some((call) => call.method === 'DELETE')).toBe(false);
  });

  test('a 400 on create surfaces the backend error and keeps the modal open', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [], calls, createStatus: 400 }));
    await gotoIncomes(page);

    await page.getByTestId('incomes-new-button').click();
    await page.locator('form input[type="text"]').first().fill('Ingreso inválido');
    await page.locator('form input[type="month"]').fill('2026-04');
    await page.getByTestId('partner-split-total').fill('100');
    await page.getByTestId('income-form-submit').click();

    await expect(page.getByText('No se pudo guardar')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Nuevo ingreso' })).toBeVisible();
  });
});
