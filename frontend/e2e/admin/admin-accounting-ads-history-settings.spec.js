/**
 * E2E tests for the ads log, audit history and notification settings.
 *
 * FLOWS: admin-accounting-ads, admin-accounting-history,
 *        admin-accounting-settings
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_ADS,
  ADMIN_ACCOUNTING_HISTORY,
  ADMIN_ACCOUNTING_SETTINGS,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const ADS_ROWS = [
  {
    id: 1,
    spend_date: '2026-01-17',
    platform: 'facebook',
    platform_label: 'Facebook Ads',
    origin_card: 'T.C 0655',
    amount: '146103.00',
    accumulated: '146103.00',
    notes: '',
    created_at: '2026-01-17T10:00:00Z',
    updated_at: '2026-01-17T10:00:00Z',
  },
  {
    id: 2,
    spend_date: '2026-01-25',
    platform: 'facebook',
    platform_label: 'Facebook Ads',
    origin_card: 'T.C 0656',
    amount: '143820.00',
    accumulated: '289923.00',
    notes: '',
    created_at: '2026-01-25T10:00:00Z',
    updated_at: '2026-01-25T10:00:00Z',
  },
];

const CHANGELOG = {
  results: [
    {
      id: 1,
      entity_type: 'income',
      entity_type_label: 'Ingreso',
      object_id: 5,
      object_repr: 'Kore - Inicio 40%',
      action: 'updated',
      action_label: 'Actualizado',
      changes: [
        {
          field: 'total_amount',
          label: 'Monto total',
          old: '1000000.00',
          new: '1160000.00',
        },
      ],
      actor: 1,
      actor_username: 'gustavo',
      created_at: '2026-07-01T15:30:00Z',
    },
  ],
  count: 25,
  page: 1,
  num_pages: 2,
};

function buildHandler({ calls }) {
  return async ({ route, apiPath, method }) => {
    const url = new URL(route.request().url());
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath === 'accounting/ads/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: ADS_ROWS, meta: {} }),
      };
    }
    if (apiPath === 'accounting/ads/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...ADS_ROWS[0], id: 99, ...body }),
      };
    }
    if (apiPath === 'accounting/change-logs/' && method === 'GET') {
      calls.push({
        apiPath,
        method,
        params: Object.fromEntries(url.searchParams.entries()),
      });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(CHANGELOG),
      };
    }
    if (apiPath === 'accounting/settings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          notification_recipients: ['gustavo@projectapp.co'],
          notifications_enabled: true,
          card_reminder_enabled: true,
          hosting_expiry_reminder_enabled: true,
          usd_exchange_rate: '4000.00',
          updated_at: '2026-07-01T00:00:00Z',
        }),
      };
    }
    if (apiPath === 'accounting/settings/update/' && method === 'PATCH') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...body,
          notifications_enabled: body.notifications_enabled ?? true,
          updated_at: '2026-07-02T00:00:00Z',
        }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

test.describe('Admin Accounting Ads, History & Settings', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('ads list shows the accumulated column', {
    tag: [...ADMIN_ACCOUNTING_ADS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/ads', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Ads', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(
      page.getByTestId('accounting-row-2').getByText('$289.923'),
    ).toBeVisible();
  });

  test('creates an ads spend through the modal', {
    tag: [...ADMIN_ACCOUNTING_ADS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/ads', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Ads', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('ads-new-button').click();
    await expect(
      page.getByRole('heading', { name: 'Nuevo gasto en Ads' }),
    ).toBeVisible();
    await page.locator('form input[type="date"]').fill('2026-07-01');
    await page.locator('form input[inputmode="numeric"]').first().fill('120000');
    await page.getByTestId('ad-spend-form-submit').click();

    await expect(page.getByText('Gasto en Ads creado')).toBeVisible();
    const create = calls.find((call) => call.method === 'POST');
    expect(create.body.spend_date).toBe('2026-07-01');
  });

  test('history renders audit rows and expands the field diff', {
    tag: [...ADMIN_ACCOUNTING_HISTORY, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/history', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Historial', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('changelog-row-1')).toBeVisible();

    await page.getByTestId('changelog-row-1').click();
    await expect(page.getByTestId('changelog-detail-1')).toBeVisible();
    await expect(page.getByText('Monto total')).toBeVisible();
    await expect(page.getByText('1000000.00')).toBeVisible();
    await expect(page.getByText('1160000.00')).toBeVisible();
  });

  test('history entity filter refires the fetch with entity_type', {
    tag: [...ADMIN_ACCOUNTING_HISTORY, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/history', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('changelog-row-1')).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('history-filter-entity').selectOption('expense');

    await expect
      .poll(() => calls.some((call) => call.params?.entity_type === 'expense'))
      .toBe(true);
  });

  test('history shows the server-side pagination summary', {
    tag: [...ADMIN_ACCOUNTING_HISTORY, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/history', { waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('history-page-info')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('history-page-info')).toContainText('Página 1 de 2');
    await expect(page.getByTestId('history-page-info')).toContainText('25 cambios');
  });

  test('settings adds a recipient and saves both emails', {
    tag: [...ADMIN_ACCOUNTING_SETTINGS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/settings', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByRole('heading', { name: 'Configuración', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('settings-recipient-input-0')).toHaveValue(
      'gustavo@projectapp.co',
    );

    await page.getByTestId('settings-add-recipient').click();
    await page.getByTestId('settings-recipient-input-1').fill('carlos@projectapp.co');
    await page.getByTestId('settings-save-button').click();

    await expect(page.getByText('Configuración guardada')).toBeVisible();
    const patch = calls.find((call) => call.method === 'PATCH');
    expect(patch.body.notification_recipients).toEqual([
      'gustavo@projectapp.co',
      'carlos@projectapp.co',
    ]);
  });

  test('settings persists the card-debt reminder toggle', {
    tag: [...ADMIN_ACCOUNTING_SETTINGS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/settings', { waitUntil: 'domcontentloaded' });

    await expect(
      page.getByText('Recordatorio de deuda de tarjetas'),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('settings-card-reminder-toggle').click();
    await page.getByTestId('settings-save-button').click();

    await expect(page.getByText('Configuración guardada')).toBeVisible();
    const patch = calls.find((call) => call.method === 'PATCH');
    expect(patch.body.card_reminder_enabled).toBe(false);
  });

  test('settings blocks saving an invalid email', {
    tag: [...ADMIN_ACCOUNTING_SETTINGS, '@role:admin'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/settings', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('settings-recipient-input-0')).toBeVisible({
      timeout: 25_000,
    });

    await page.getByTestId('settings-recipient-input-0').fill('no-es-un-email');
    await page.getByTestId('settings-save-button').click();

    expect(calls.some((call) => call.method === 'PATCH')).toBe(false);
  });
});
