/**
 * E2E tests for the accounting card snapshots subview.
 *
 * FLOW: admin-accounting-cards
 * Covers: list rendering with debt chip, create via modal (date defaults
 *         to today), edit prefill and delete with confirmation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_CARDS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function snapshotRow(overrides = {}) {
  return {
    id: 1,
    card_name: 'T.C 0064',
    snapshot_date: '2026-06-17',
    available_amount: '413226.00',
    debt_amount: '7586774.00',
    notes: '',
    created_at: '2026-06-17T10:00:00Z',
    updated_at: '2026-06-17T10:00:00Z',
    ...overrides,
  };
}

const DEFAULT_CATALOG = [
  {
    id: 1,
    name: 'T.C 0064',
    credit_limit: '8000000.00',
    is_active: true,
    statements_since: '2026-05-01',
  },
];

function buildHandler({ rows, calls, catalog = DEFAULT_CATALOG, savedTabs = [] }) {
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
    if (apiPath === 'accounting/card-snapshots/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: rows, meta: {} }),
      };
    }
    if (apiPath === 'accounting/credit-cards/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: catalog, meta: {} }),
      };
    }
    if (apiPath === 'accounting/card-snapshots/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ method, apiPath, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(snapshotRow({ id: 99, ...body })),
      };
    }
    if (/^accounting\/card-snapshots\/\d+\/update\/$/.test(apiPath) && method === 'PATCH') {
      const body = route.request().postDataJSON();
      calls.push({ method, apiPath, body });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(snapshotRow({ ...rows[0], ...body })),
      };
    }
    if (/^accounting\/card-snapshots\/\d+\/delete\/$/.test(apiPath) && method === 'DELETE') {
      calls.push({ method, apiPath });
      return { status: 204, contentType: 'application/json', body: '' };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(savedTabs),
      };
    }
    return null;
  };
}

async function gotoCards(page) {
  await page.goto('/panel/accounting/cards', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Tarjetas', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
}

test.describe('Admin Accounting Cards', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('defaults the card filter to the registered catalog cards', {
    tag: [...ADMIN_ACCOUNTING_CARDS, '@role:admin'],
  }, async ({ page }) => {
    // T.C 0655 exists only in old snapshots — not in the catalog.
    await mockApi(page, buildHandler({
      rows: [
        snapshotRow(),
        snapshotRow({ id: 2, snapshot_date: '2026-07-01', debt_amount: '4150954.00' }),
        snapshotRow({ id: 3, card_name: 'T.C 0655', snapshot_date: '2026-06-20', debt_amount: '1000000.00' }),
      ],
      calls: [],
    }));
    await gotoCards(page);

    // Default view: only the registered card's snapshots, with the filter
    // visible as a removable chip (not a silent cut).
    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(page.getByTestId('accounting-row-2')).toBeVisible();
    await expect(page.getByTestId('accounting-row-3')).toHaveCount(0);
    await expect(page.getByTestId('accounting-filter-chip')).toHaveText(/T\.C 0064/);
    await expect(page.getByTestId('cards-total-debt')).toContainText('4.150.954');

    // Clearing the filter surfaces the historical card again.
    await page.getByTestId('accounting-filter-reset').click();
    await expect(page.getByTestId('accounting-row-3')).toBeVisible();
    // Latest per card: 4.150.954 (T.C 0064, jul 1) + 1.000.000 (T.C 0655).
    await expect(page.getByTestId('cards-total-debt')).toContainText('5.150.954');
  });

  test('card filter options combine the catalog and historical names', {
    tag: [...ADMIN_ACCOUNTING_CARDS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({
      rows: [snapshotRow({ card_name: 'T.C 0655' })],
      calls: [],
      catalog: [
        ...DEFAULT_CATALOG,
        // Registered but with no snapshots yet: filterable anyway.
        {
          id: 2,
          name: 'T.C 9999',
          credit_limit: '2000000.00',
          is_active: true,
          statements_since: null,
        },
      ],
    }));
    await gotoCards(page);

    await page.getByRole('button', { name: /Filtros/ }).click();
    // ^ anchor: the preselection chips are named "Quitar filtro Tarjeta: …"
    // and would otherwise match too.
    await page
      .getByTestId('accounting-filter-panel')
      .getByRole('button', { name: /^Tarjeta/ })
      .click();

    await expect(page.getByRole('checkbox', { name: 'T.C 0064' })).toBeVisible();
    await expect(page.getByRole('checkbox', { name: 'T.C 9999' })).toBeVisible();
    await expect(page.getByRole('checkbox', { name: 'T.C 0655' })).toBeVisible();
  });

  test('a saved tab in the URL wins over the default card filter', {
    tag: [...ADMIN_ACCOUNTING_CARDS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({
      rows: [
        snapshotRow(),
        snapshotRow({ id: 3, card_name: 'T.C 0655', snapshot_date: '2026-06-20', debt_amount: '1000000.00' }),
      ],
      calls: [],
      savedTabs: [{ id: 7, name: 'Deudas altas', filters: { debtMin: '900000' } }],
    }));
    await page.goto('/panel/accounting/cards?accounting_cardsTab=7', {
      waitUntil: 'domcontentloaded',
    });
    await expect(
      page.getByRole('heading', { name: 'Tarjetas', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    // The tab's own filters apply; the catalog preselection must not
    // overwrite them, so the unregistered card's row stays visible.
    await expect(page.getByTestId('accounting-row-3')).toBeVisible();
    await expect(
      page.getByTestId('accounting-filter-chip').filter({ hasText: 'T.C 0064' }),
    ).toHaveCount(0);
  });

  test('creates a snapshot with today as the default date', {
    tag: [...ADMIN_ACCOUNTING_CARDS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [], calls }));
    await gotoCards(page);

    await page.getByTestId('cards-new-button').click();
    await expect(
      page.getByRole('heading', { name: 'Nuevo Registro de Tarjeta' }),
    ).toBeVisible();

    const dateValue = await page.locator('form input[type="date"]').inputValue();
    expect(dateValue).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    // Single catalog card: the dropdown preselects it.
    await expect(page.getByTestId('card-snapshot-card-select')).toHaveValue('T.C 0064');
    await page.locator('form input[inputmode="numeric"]').fill('500000');
    // Debt is server-computed; the form only previews it.
    await expect(page.getByTestId('card-snapshot-debt-preview')).toContainText('7.500.000');
    await page.getByTestId('card-snapshot-form-submit').click();

    await expect(page.getByText('Registro de tarjeta creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.card_name).toBe('T.C 0064');
    expect(calls[0].body.debt_amount).toBeUndefined();
    expect(Number(calls[0].body.available_amount)).toBe(500000);
  });

  test('edit prefills and PATCHes; delete asks for confirmation', {
    tag: [...ADMIN_ACCOUNTING_CARDS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ rows: [snapshotRow()], calls }));
    await gotoCards(page);

    await page.getByTestId('accounting-edit-1').click();
    await expect(
      page.getByRole('heading', { name: 'Editar Registro de Tarjeta' }),
    ).toBeVisible();
    await expect(page.getByTestId('card-snapshot-card-select')).toHaveValue('T.C 0064');
    await page.locator('form input[inputmode="numeric"]').fill('1000000');
    await page.getByTestId('card-snapshot-form-submit').click();
    await expect(page.getByText('Registro de tarjeta actualizado')).toBeVisible();
    expect(calls[0].method).toBe('PATCH');

    await page.getByTestId('accounting-delete-1').click();
    await expect(page.getByText('Eliminar registro de tarjeta')).toBeVisible();
    await page.getByTestId('confirm-modal-confirm').click();
    await expect(page.getByText('Registro de tarjeta eliminado')).toBeVisible();
    expect(calls.some((call) => call.method === 'DELETE')).toBe(true);
  });
});
