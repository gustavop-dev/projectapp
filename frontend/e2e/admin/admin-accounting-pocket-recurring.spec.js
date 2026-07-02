/**
 * E2E tests for the pocket ledger and recurring payments subviews.
 *
 * FLOWS: admin-accounting-pocket, admin-accounting-recurring
 * Covers: pocket balance card, running-balance ledger, auto-managed
 *         movement protection; recurring totals cards and the
 *         currency-dependent COP-equivalent field in the modal.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_POCKET,
  ADMIN_ACCOUNTING_RECURRING,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const POCKET_ROWS = [
  {
    id: 1,
    concept: 'Ingreso: Vastago (Fase 1) - Inicio 40%',
    movement_date: '2026-04-29',
    direction: 'in',
    direction_label: 'Ingreso',
    amount: '2123000.00',
    is_auto_managed: true,
    notes: '',
    created_at: '2026-04-29T10:00:00Z',
    updated_at: '2026-04-29T10:00:00Z',
  },
  {
    id: 2,
    concept: 'Pago T.C Rappi',
    movement_date: '2026-05-06',
    direction: 'out',
    direction_label: 'Egreso',
    amount: '2272000.00',
    is_auto_managed: false,
    notes: '',
    created_at: '2026-05-06T10:00:00Z',
    updated_at: '2026-05-06T10:00:00Z',
  },
];

const RECURRING_ROWS = [
  {
    id: 1,
    name: 'Claude Code 20x',
    price: '200.00',
    currency: 'USD',
    cop_equivalent: '800000.00',
    payment_method: 'credit_card',
    payment_method_label: 'T.C',
    frequency: 'monthly',
    frequency_label: 'Mensual',
    billing_day: 8,
    cost_type: 'fixed',
    cost_type_label: 'Fijo',
    monthly_cop_cost: '800000.00',
    is_active: true,
    notes: '',
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-01-01T10:00:00Z',
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
    if (apiPath === 'accounting/pocket/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: POCKET_ROWS,
          meta: { balance: '-149000.00' },
        }),
      };
    }
    if (apiPath === 'accounting/recurring/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: RECURRING_ROWS,
          meta: { monthly_cop_total: '800000.00' },
        }),
      };
    }
    if (apiPath === 'accounting/recurring/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...RECURRING_ROWS[0], id: 99, ...body }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

test.describe('Admin Accounting Pocket & Recurring', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('pocket balance card shows the ledger balance', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/pocket', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Bolsillo ProjectApp' }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('pocket-balance')).toBeVisible();
    await expect(page.getByText('Saldo del bolsillo')).toBeVisible();
  });

  test('ledger renders movements with a running balance column', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/pocket', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('accounting-row-1')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByRole('columnheader', { name: 'Saldo' })).toBeVisible();
    await expect(page.getByText('Pago T.C Rappi')).toBeVisible();
  });

  test('auto-managed movements warn instead of opening the edit modal', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/pocket', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('accounting-row-1')).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('accounting-edit-1').click();

    await expect(page.getByText('Movimiento automático')).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'Editar movimiento de bolsillo' }),
    ).toHaveCount(0);
  });

  test('recurring subview shows monthly cost and breakdown cards', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Contabilidad — Pagos recurrentes' }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByText('Costo mensual (COP)')).toBeVisible();
    await expect(page.getByText('Por frecuencia')).toBeVisible();
    await expect(page.getByText('Por método de pago')).toBeVisible();
    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
  });

  test('cop_equivalent field only appears for USD payments in the modal', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Contabilidad — Pagos recurrentes' }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-new-button').click();
    await expect(
      page.getByRole('heading', { name: 'Nuevo pago recurrente' }),
    ).toBeVisible();

    // COP by default: no COP-equivalent field.
    await expect(page.getByText('Equivalente COP')).toHaveCount(0);

    await page.getByRole('tab', { name: 'USD' }).click();
    await expect(page.getByText('Equivalente COP')).toBeVisible();
  });

  test('creates a recurring payment through the modal', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Contabilidad — Pagos recurrentes' }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-new-button').click();
    await page.locator('form input[type="text"]').first().fill('Netflix');
    await page.locator('form input[type="number"]').first().fill('39800');
    await page.getByTestId('recurring-payment-form-submit').click();

    await expect(page.getByText('Pago recurrente creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.name).toBe('Netflix');
  });
});
