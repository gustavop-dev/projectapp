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

function buildHandler({ rows, calls }) {
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
      return { status: 200, contentType: 'application/json', body: '[]' };
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

  test('renders snapshots with the latest-debt chip', {
    tag: [...ADMIN_ACCOUNTING_CARDS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({
      rows: [
        snapshotRow(),
        snapshotRow({ id: 2, snapshot_date: '2026-07-01', debt_amount: '4150954.00' }),
        snapshotRow({ id: 3, card_name: 'T.C 0655', snapshot_date: '2026-06-20', debt_amount: '1000000.00' }),
      ],
      calls,
    }));
    await gotoCards(page);

    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    // Latest per card: 4.150.954 (T.C 0064, jul 1) + 1.000.000 (T.C 0655).
    await expect(page.getByTestId('cards-total-debt')).toContainText('5.150.954');
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

    await page.locator('form input[type="text"]').first().fill('T.C 0064');
    const numbers = page.locator('form input[inputmode="numeric"]');
    await numbers.nth(0).fill('500000');
    await numbers.nth(1).fill('7500000');
    await page.getByTestId('card-snapshot-form-submit').click();

    await expect(page.getByText('Registro de tarjeta creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.card_name).toBe('T.C 0064');
    expect(Number(calls[0].body.debt_amount)).toBe(7500000);
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
    await expect(page.locator('form input[type="text"]').first()).toHaveValue('T.C 0064');
    const numbers = page.locator('form input[inputmode="numeric"]');
    await numbers.nth(1).fill('7000000');
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
