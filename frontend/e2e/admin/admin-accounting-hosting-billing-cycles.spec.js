/**
 * E2E tests for the hosting row actions on /panel/accounting/hostings.
 *
 * FLOWS: admin-accounting-hosting-billing, admin-accounting-hosting-cycles
 * Covers: paper-plane cuenta de cobro send (email gate, confirm preview,
 *         success + email-failure toasts, "Cobro enviado" badge) and the
 *         cycles modal (history with backfill badge, register payment,
 *         delete cycle with confirm).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_HOSTING_BILLING,
  ADMIN_ACCOUNTING_HOSTING_CYCLES,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function hostingRows({ billingSent }) {
  return [
    {
      id: 1,
      client_name: 'German - Kore',
      client_email: 'german@korehealths.com',
      domain_url: 'https://korehealths.com/',
      monthly_value: '91667.00',
      payment_modality: 'semiannual',
      payment_modality_label: 'Semestral',
      benefit: '',
      valid_from: '2026-03-02',
      valid_to: '2026-09-02',
      cycles_count: 1,
      payment_per_cycle: '550002.00',
      total_paid: '550002.00',
      billing_requested_at: billingSent ? '2026-07-16T10:00:00Z' : null,
      is_active: true,
      notes: '',
      created_at: '2026-03-02T10:00:00Z',
      updated_at: '2026-03-02T10:00:00Z',
    },
    {
      id: 2,
      client_name: 'Nestor - Xpandia',
      client_email: '',
      domain_url: 'https://xpandia.global/',
      monthly_value: '19000.00',
      payment_modality: 'annual',
      payment_modality_label: 'Anual',
      benefit: '',
      valid_from: '2026-07-01',
      valid_to: '2027-07-01',
      cycles_count: 0,
      payment_per_cycle: '228000.00',
      total_paid: '0.00',
      billing_requested_at: null,
      is_active: true,
      notes: '',
      created_at: '2026-07-01T10:00:00Z',
      updated_at: '2026-07-01T10:00:00Z',
    },
  ];
}

const BACKFILL_CYCLE = {
  id: 10,
  paid_at: '2026-01-02',
  modality: 'semiannual',
  modality_label: 'Semestral',
  amount: '550002.00',
  period_from: '2025-07-02',
  period_to: '2026-01-02',
  is_backfill: true,
  cycles_represented: 3,
  notes: 'Backfill histórico',
};

function buildHandler({ calls, emailSent = true, cycles = [] }) {
  const state = { billingSent: false, cycles: [...cycles] };
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
    if (apiPath === 'accounting/hostings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: hostingRows({ billingSent: state.billingSent }),
          meta: {
            active_count: 2,
            monthly_income: '110667.00',
            expiring_soon_count: 0,
            total_paid: '550002.00',
          },
        }),
      };
    }
    if (
      apiPath === 'accounting/hostings/1/send-collection-account/'
      && method === 'POST'
    ) {
      calls.push({ apiPath, method });
      state.billingSent = true;
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          document: { id: 77, public_number: 'PA-2026-0007' },
          email_sent: emailSent,
        }),
      };
    }
    if (apiPath === 'accounting/hostings/1/cycles/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: state.cycles }),
      };
    }
    if (
      apiPath === 'accounting/hostings/1/cycles/create/'
      && method === 'POST'
    ) {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      const cycle = {
        ...BACKFILL_CYCLE,
        id: 50,
        paid_at: body.paid_at,
        amount: String(body.amount),
        is_backfill: false,
        cycles_represented: 1,
        notes: body.notes || '',
      };
      state.cycles = [cycle, ...state.cycles];
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          cycle,
          hosting: {
            ...hostingRows({ billingSent: state.billingSent })[0],
            cycles_count: state.cycles.length,
          },
        }),
      };
    }
    if (
      apiPath === 'accounting/hostings/1/cycles/10/delete/'
      && method === 'DELETE'
    ) {
      calls.push({ apiPath, method });
      state.cycles = state.cycles.filter((cycle) => cycle.id !== 10);
      return { status: 204, contentType: 'application/json', body: '' };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function gotoHostings(page) {
  await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Hostings', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
  await expect(page.getByTestId('accounting-row-1')).toBeVisible();
}

test.describe('Admin Accounting Hosting Billing', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('the send action requires a client email', {
    tag: [...ADMIN_ACCOUNTING_HOSTING_BILLING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoHostings(page);

    await expect(page.getByTestId('hosting-send-billing-1')).toBeEnabled();
    await expect(page.getByTestId('hosting-send-billing-2')).toBeDisabled();
  });

  test('sending the cuenta de cobro confirms, POSTs and shows the badge', {
    tag: [...ADMIN_ACCOUNTING_HOSTING_BILLING, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoHostings(page);

    await page.getByTestId('hosting-send-billing-1').click();
    await expect(
      page.getByRole('heading', { name: 'Enviar cuenta de cobro' }),
    ).toBeVisible();

    await page.getByRole('button', { name: 'Enviar al cliente' }).click();

    await expect(page.getByText('Cuenta de cobro enviada')).toBeVisible();
    await expect(page.getByText('Cobro enviado')).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/hostings/1/send-collection-account/',
      method: 'POST',
    });
  });

  test('a failed email keeps the document issued and warns the user', {
    tag: [...ADMIN_ACCOUNTING_HOSTING_BILLING, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [], emailSent: false }));
    await gotoHostings(page);

    await page.getByTestId('hosting-send-billing-1').click();
    await page.getByRole('button', { name: 'Enviar al cliente' }).click();

    await expect(
      page.getByText('Cuenta de cobro emitida, pero el correo falló'),
    ).toBeVisible();
  });
});

test.describe('Admin Accounting Hosting Cycles', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('opens the history with the consolidated backfill badge', {
    tag: [...ADMIN_ACCOUNTING_HOSTING_CYCLES, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(
      page,
      buildHandler({ calls: [], cycles: [BACKFILL_CYCLE] }),
    );
    await gotoHostings(page);

    await page.getByTestId('hosting-cycles-1').click();

    await expect(
      page.getByRole('heading', { name: 'Ciclos de pago — German - Kore' }),
    ).toBeVisible();
    await expect(page.getByText('histórico × 3')).toBeVisible();
    await expect(page.getByText('Extender vigencia')).toBeVisible();
  });

  test('registers a cycle payment from the prefilled form', {
    tag: [...ADMIN_ACCOUNTING_HOSTING_CYCLES, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, cycles: [BACKFILL_CYCLE] }));
    await gotoHostings(page);

    await page.getByTestId('hosting-cycles-1').click();
    await page.getByTestId('cycle-amount').fill('600000');
    await page.getByTestId('cycle-submit').click();

    await expect(page.getByText('Pago de ciclo registrado')).toBeVisible();
    await expect(page.getByText('$600.000')).toBeVisible();
    const createCall = calls.find(
      (call) => call.apiPath === 'accounting/hostings/1/cycles/create/',
    );
    expect(createCall.body.advance_validity).toBe(true);
  });

  test('deletes a cycle after the confirm warns about recalculation', {
    tag: [...ADMIN_ACCOUNTING_HOSTING_CYCLES, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, cycles: [BACKFILL_CYCLE] }));
    await gotoHostings(page);

    await page.getByTestId('hosting-cycles-1').click();
    await page.getByLabel('Eliminar ciclo').click();
    await expect(
      page.getByRole('heading', { name: 'Eliminar ciclo' }),
    ).toBeVisible();

    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Ciclo eliminado')).toBeVisible();
    await expect(
      page.getByText('Sin ciclos registrados todavía.'),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/hostings/1/cycles/10/delete/',
      method: 'DELETE',
    });
  });
});
