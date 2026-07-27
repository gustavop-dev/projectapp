/**
 * E2E tests for inline editing of statement transaction rows.
 *
 * FLOWS: admin-accounting-statements
 * Covers: dblclick inline merchant edit on a draft statement (PATCH body +
 *         updated cell), and the processed gate (no editor opens).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_STATEMENTS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function statusPayload() {
  return {
    year: 2026,
    year_options: [2026],
    months: [
      {
        period: '2026-05',
        label: 'mayo',
        applies: true,
        statements: [
          { id: 1, card_name: 'T.C 0064', status: 'processed', status_label: 'Procesado' },
        ],
      },
      {
        period: '2026-06',
        label: 'junio',
        applies: true,
        statements: [
          { id: 2, card_name: 'T.C 0064', status: 'draft', status_label: 'Borrador' },
        ],
      },
    ],
  };
}

function makeTx(overrides = {}) {
  return {
    id: 10,
    transaction_date: '2026-06-05',
    raw_description: 'PAGO SERVIDOR HETZNER',
    merchant_name: 'Hetzner',
    amount: '450000.00',
    category: 'software',
    category_label: 'Software y suscripciones',
    installment_label: '',
    original_amount: null,
    original_currency: '',
    is_identified: true,
    ...overrides,
  };
}

function makeDetail(overrides = {}) {
  return {
    id: 2,
    card_name: 'T.C 0064',
    period: '2026-06',
    period_label: 'Junio 2026',
    status: 'draft',
    status_label: 'Borrador',
    purchases_total: '450000.00',
    payments_total: '0.00',
    interest_and_fees: '0.00',
    minimum_payment: '45000.00',
    closing_balance: '450000.00',
    due_date: '2026-07-05',
    created_at: '2026-07-01T10:00:00Z',
    pdf_file_url: null,
    category_totals: [],
    transactions: [makeTx()],
    ...overrides,
  };
}

function buildHandler({ calls }) {
  const state = { detail: makeDetail() };
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
    if (apiPath.startsWith('accounting/statements/status/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(statusPayload()),
      };
    }
    if (apiPath === 'accounting/statements/1/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(makeDetail({
          id: 1,
          period: '2026-05',
          period_label: 'Mayo 2026',
          status: 'processed',
          status_label: 'Procesado',
        })),
      };
    }
    if (apiPath === 'accounting/statements/2/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(state.detail),
      };
    }
    if (
      apiPath === 'accounting/statements/2/transactions/10/update/'
      && method === 'PATCH'
    ) {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      const updated = { ...state.detail.transactions[0], ...body };
      state.detail = makeDetail({ transactions: [updated] });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(updated),
      };
    }
    if (apiPath.startsWith('accounting/merchant-aliases')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], meta: {} }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function gotoStatements(page) {
  await page.goto('/panel/accounting/statements', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Extractos de tarjeta' }),
  ).toBeVisible({ timeout: 25_000 });
}

test.describe('Admin Accounting Statements: inline row editing', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('dblclick edits the merchant of a draft row and PATCHes it', {
    tag: [...ADMIN_ACCOUNTING_STATEMENTS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoStatements(page);

    await page.getByTestId('statement-chip-2').click();
    await expect(page.getByTestId('statement-detail')).toBeVisible();

    const cell = page.getByTestId('tx-cell-merchant_name-10');
    await cell.getByTestId('inline-cell-display').dblclick();
    const input = cell.locator('input');
    await input.fill('Hetzner Cloud');
    await input.press('Enter');

    await expect(cell).toContainText('Hetzner Cloud');
    const patchCall = calls.find(
      (call) => call.apiPath === 'accounting/statements/2/transactions/10/update/',
    );
    expect(patchCall.body).toEqual({
      merchant_name: 'Hetzner Cloud',
      is_identified: true,
    });
  });

  test('a processed statement opens no inline editor on dblclick', {
    tag: [...ADMIN_ACCOUNTING_STATEMENTS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoStatements(page);

    await page.getByTestId('statement-chip-1').click();
    await expect(page.getByTestId('statement-detail')).toBeVisible();

    const cell = page.getByTestId('tx-cell-merchant_name-10');
    await expect(cell).toContainText('Hetzner');
    await cell.dblclick();

    await expect(cell.locator('input')).toHaveCount(0);
    await expect(cell.getByTestId('inline-cell-display')).toHaveCount(0);
  });
});
