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
    paid_amount: '0.00',
    pending_amount: '1160000.00',
    payment_status: 'pending',
    payment_status_label: 'Pendiente',
    notes: '',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
    ...overrides,
  };
}

function buildHandler({
  rows, calls, createStatus = 201, meta = {}, listFetches = { count: 0 },
}) {
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
      listFetches.count += 1;
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: rows, meta }),
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
      // The page refetches after every mutation (a row's payment state is
      // computed from other rows), so the mock has to drop it like the
      // server would, or the refetch would resurrect it.
      const id = Number(apiPath.split('/')[2]);
      const index = rows.findIndex((row) => row.id === id);
      if (index !== -1) rows.splice(index, 1);
      return { status: 204, contentType: 'application/json', body: '' };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function openFilterPanel(page) {
  // The toggle carries an active-filter count, so match loosely.
  await page.getByRole('button', { name: /Filtros/ }).click();
}

// Column headers share names with filter options, so scope to the panel.
function filterPanel(page) {
  return page.getByTestId('accounting-filter-panel');
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

    await page.getByTestId('income-form-concept').fill('Vastago (Fase 1) - Inicio 40%');
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

    await page.getByTestId('income-form-concept').fill('Universidad Nacional');
    await page.locator('form input[type="month"]').fill('2026-02');
    await page.getByRole('tab', { name: 'Personal Gustavo' }).click();

    // Personal ledger swaps the partner split for a single value input.
    await expect(page.getByTestId('partner-split-total')).toHaveCount(0);
    await page.locator('form input[inputmode="numeric"]').fill('1400000');
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
    await expect(page.getByTestId('income-form-concept')).toHaveValue('Kore - Inicio 40%');

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
    await page.getByTestId('income-form-concept').fill('Ingreso inválido');
    await page.locator('form input[type="month"]').fill('2026-04');
    await page.getByTestId('partner-split-total').fill('100');
    await page.getByTestId('income-form-submit').click();

    await expect(page.getByText('No se pudo guardar')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Nuevo ingreso' })).toBeVisible();
  });
});

test.describe('Admin Accounting Incomes: liquidation, write-off and paid state', () => {
  const paidRow = () => incomeRow({
    id: 10,
    concept: 'Kore - Pagado',
    paid_amount: '1160000.00',
    pending_amount: '0.00',
    payment_status: 'paid',
    payment_status_label: 'Pagado',
  });

  const partialRow = () => incomeRow({
    id: 11,
    concept: 'Kore - Parcial',
    total_amount: '1000000.00',
    paid_amount: '400000.00',
    pending_amount: '600000.00',
    payment_status: 'partial',
    payment_status_label: 'Parcial',
  });

  const lostRow = () => incomeRow({
    id: 12,
    concept: 'Catherine Ruiz Candles',
    kind: 'lost',
    kind_label: 'Perdido',
    total_amount: '460000.00',
    paid_amount: null,
    pending_amount: null,
    payment_status: null,
    payment_status_label: null,
  });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('tints paid and partial rows and shows what is still missing', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({
      rows: [incomeRow(), paidRow(), partialRow()],
      calls: [],
    }));
    await gotoIncomes(page);

    await expect(page.getByTestId('accounting-row-10')).toHaveClass(/bg-success-soft/);
    await expect(page.getByTestId('accounting-row-11')).toHaveClass(/bg-warning-soft/);
    // Pending rows stay neutral.
    await expect(page.getByTestId('accounting-row-1')).toHaveClass(/bg-surface/);

    await expect(page.getByTestId('income-payment-10')).toContainText('Pagado');
    await expect(page.getByTestId('income-payment-11')).toContainText('Parcial');
    await expect(page.getByTestId('income-payment-11')).toContainText('600.000');
  });

  test('hides written-off income until the Pérdidas filter is used', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({
      rows: [incomeRow(), lostRow()],
      calls: [],
      meta: { lost_total: '460000.00' },
    }));
    await gotoIncomes(page);

    // "Todos" is the working set: the lost row is out.
    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(page.getByTestId('accounting-row-12')).toHaveCount(0);

    await openFilterPanel(page);
    await filterPanel(page).getByRole('tab', { name: 'Pérdidas' }).click();

    await expect(page.getByTestId('accounting-row-12')).toBeVisible();
    await expect(page.getByTestId('accounting-row-1')).toHaveCount(0);
    await expect(page.getByTestId('incomes-total-lost')).toContainText('460.000');
  });

  test('liquidating prefills the pending amount and keeps the expected row', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    const listFetches = { count: 0 };
    await mockApi(page, buildHandler({
      rows: [partialRow()], calls, listFetches,
    }));
    await gotoIncomes(page);

    await page.getByTestId('income-liquidate-11').click();
    await expect(
      page.getByRole('heading', { name: 'Liquidar ingreso esperado' }),
    ).toBeVisible();
    // Defaults to what is still owed, not the full projection.
    await expect(page.getByTestId('partner-split-total')).toHaveValue('600.000');

    await page.getByTestId('income-liquidate-period').fill('2026-11');
    await page.getByTestId('income-liquidate-submit').click();

    await expect.poll(() => calls.filter((c) => c.method === 'POST').length)
      .toBe(1);
    const body = calls.find((c) => c.method === 'POST').body;
    expect(body.kind).toBe('liquid');
    expect(body.expected_income).toBe(11);
    expect(body.period_date).toBe('2026-11');

    // The parent's paid state is server-computed, so the list must refetch.
    await expect.poll(() => listFetches.count).toBeGreaterThan(1);
    await expect(page.getByTestId('accounting-row-11')).toBeVisible();
  });

  test('writes off a pending expected income', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [incomeRow()], calls }));
    await gotoIncomes(page);

    await page.getByTestId('income-write-off-1').click();
    await page.getByRole('button', { name: 'Marcar como perdido' }).last().click();

    await expect.poll(() => calls.filter((c) => c.method === 'PATCH').length)
      .toBe(1);
    const body = calls.find((c) => c.method === 'PATCH').body;
    expect(body.kind).toBe('lost');
    expect(body.destination).toBe('partners');
  });

  test('offers no write-off on an already collected income', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    // The server rejects writing off a row with liquidations, so the
    // action must not be offered for paid or partial rows.
    await mockApi(page, buildHandler({
      rows: [paidRow(), partialRow()], calls: [],
    }));
    await gotoIncomes(page);

    await expect(page.getByTestId('income-liquidate-10')).toBeVisible();
    await expect(page.getByTestId('income-write-off-10')).toHaveCount(0);
    await expect(page.getByTestId('income-write-off-11')).toHaveCount(0);
  });

  test('shows no row actions on a written-off income', {
    tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ rows: [lostRow()], calls: [] }));
    await gotoIncomes(page);

    await openFilterPanel(page);
    await filterPanel(page).getByRole('tab', { name: 'Pérdidas' }).click();

    await expect(page.getByTestId('accounting-row-12')).toBeVisible();
    await expect(page.getByTestId('income-liquidate-12')).toHaveCount(0);
    await expect(page.getByTestId('income-write-off-12')).toHaveCount(0);
  });
});
