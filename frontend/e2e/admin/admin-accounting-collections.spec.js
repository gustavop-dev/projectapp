/**
 * E2E tests for the cobros monitor at /panel/accounting/collections.
 *
 * FLOWS: admin-accounting-collections
 * Covers: status counters from list meta, the segmented Vencidas filter with
 *         the is_overdue badge, mark-paid and cancel behind ConfirmModal, and
 *         resend to the client.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_COLLECTIONS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function makeRows() {
  return [
    {
      id: 1,
      public_number: 'PA-2026-0001',
      origin_label: 'Hosting',
      customer_name: 'German - Kore',
      total: '550002.00',
      issue_date: '2026-06-01',
      due_date: '2026-06-15',
      commercial_status: 'issued',
      commercial_status_label: 'Emitida',
      is_overdue: true,
    },
    {
      id: 2,
      public_number: 'PA-2026-0002',
      origin_label: 'Hosting',
      customer_name: 'Nestor - Xpandia',
      total: '550002.00',
      issue_date: '2026-07-10',
      due_date: '2026-07-30',
      commercial_status: 'issued',
      commercial_status_label: 'Emitida',
      is_overdue: false,
    },
    {
      id: 3,
      public_number: 'PA-2026-0003',
      origin_label: 'Hosting',
      customer_name: 'Laura - Mi Huella',
      total: '550002.00',
      issue_date: '2026-05-01',
      due_date: '2026-05-15',
      commercial_status: 'paid',
      commercial_status_label: 'Pagada',
      is_overdue: false,
    },
  ];
}

const META = {
  issued_count: 2,
  issued_total: '1100004.00',
  paid_count: 1,
  paid_total: '550002.00',
  cancelled_count: 0,
};

function buildHandler({ calls }) {
  const state = { rows: makeRows() };
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
    if (apiPath.startsWith('accounting/collection-accounts/') && method === 'POST') {
      const match = apiPath.match(
        /^accounting\/collection-accounts\/(\d+)\/(mark-paid|cancel|resend)\/$/,
      );
      if (match) {
        const [, id, action] = match;
        calls.push({ apiPath, method });
        const row = state.rows.find((item) => item.id === Number(id));
        if (action === 'mark-paid') {
          Object.assign(row, {
            commercial_status: 'paid',
            commercial_status_label: 'Pagada',
            is_overdue: false,
          });
        }
        if (action === 'cancel') {
          Object.assign(row, {
            commercial_status: 'cancelled',
            commercial_status_label: 'Anulada',
            is_overdue: false,
          });
        }
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(row),
        };
      }
    }
    if (apiPath.startsWith('accounting/collection-accounts/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: state.rows, meta: META }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function gotoCollections(page) {
  await page.goto('/panel/accounting/collections', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Cobros', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
  await expect(page.getByTestId('accounting-row-1')).toBeVisible();
}

test.describe('Admin Accounting Collections', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('the status counters combine list meta and overdue rows', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoCollections(page);

    await expect(page.getByTestId('accounting-stat-value')).toHaveText([
      '2', '1', '1', '0',
    ]);
    await expect(page.getByText('Por cobrar: $1.100.004')).toBeVisible();
    await expect(page.getByText('Recaudado: $550.002')).toBeVisible();
  });

  test('the Vencidas filter keeps only overdue rows with their badge', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoCollections(page);

    await page.getByRole('tab', { name: 'Vencidas' }).click();

    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(page.getByTestId('accounting-row-2')).toHaveCount(0);
    await expect(
      page.getByTestId('accounting-row-1').getByText('Vencida', { exact: true }),
    ).toBeVisible();
  });

  test('marking an issued account as paid confirms and updates the badge', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('accounting-row-2').getByLabel('Marcar pagada').click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(
      page.getByTestId('accounting-row-2').getByText('Pagada', { exact: true }),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/collection-accounts/2/mark-paid/',
      method: 'POST',
    });
  });

  test('cancelling an issued account confirms and shows Anulada', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('accounting-row-2').getByLabel('Anular').click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(
      page.getByTestId('accounting-row-2').getByText('Anulada', { exact: true }),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/collection-accounts/2/cancel/',
      method: 'POST',
    });
  });

  test('resending a paid account notifies without a confirm step', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('accounting-row-3').getByLabel('Reenviar al cliente').click();

    await expect(
      page.getByText('Cuenta de cobro reenviada al cliente'),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/collection-accounts/3/resend/',
      method: 'POST',
    });
  });
});
