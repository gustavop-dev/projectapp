import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_COLLECTIONS,
  ADMIN_ACCOUNTING_HOSTINGS,
  ADMIN_ACCOUNTING_INCOME_CRUD,
} from '../helpers/flow-tags.js';
import { waitForNuxtApp } from '../helpers/navigation.js';

test.setTimeout(60_000);

const PROJECT_ID = 10;

const hosting = {
  id: 101,
  client: 5,
  client_display_name: 'Ana Pérez',
  billing_email: 'ana@acme.co',
  client_name: 'Ana Pérez - Acme',
  project: PROJECT_ID,
  project_name: 'Kore',
  domain_url: 'https://acme.test/',
  monthly_value: '91667.00',
  payment_modality: 'semiannual',
  payment_modality_label: 'Semestral',
  benefit: '',
  valid_from: '2026-03-02',
  valid_to: '2026-09-02',
  cycles_count: 1,
  payment_per_cycle: '550002.00',
  total_paid: '0.00',
  is_active: true,
  notes: '',
  created_at: '2026-03-02T10:00:00Z',
  updated_at: '2026-03-02T10:00:00Z',
};

const income = {
  id: 201,
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
  client: 5,
  client_name: 'Ana Pérez',
  project: PROJECT_ID,
  project_name: 'Kore',
  origin: 'development',
  origin_label: 'Desarrollo',
  notes: '',
  created_at: '2026-02-01T10:00:00Z',
  updated_at: '2026-02-01T10:00:00Z',
};

const collection = {
  id: 301,
  public_number: 'PA-ACME-001',
  origin: 'income',
  origin_label: 'Ingreso',
  customer_name: 'Acme Soluciones',
  client: 5,
  client_display_name: 'Ana Pérez',
  project_id: PROJECT_ID,
  project_name: 'Kore',
  total: '1160000.00',
  issue_date: '2026-02-01',
  due_date: '2026-02-15',
  commercial_status: 'issued',
  commercial_status_label: 'Emitida',
  is_overdue: false,
  can_delete: false,
};

function buildHandler(calls) {
  return async ({ apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath === 'accounts/session-token-bridge/' && method === 'POST') {
      calls.push({ apiPath, method });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tokens: { access: 'e2e-platform-access', refresh: 'e2e-platform-refresh' },
          user: { id: 9001, role: 'admin', email: 'admin@e2e.test' },
        }),
      };
    }
    if (apiPath === 'accounting/settings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          income_default_view_mode: 'classic',
          collection_accounts_view_mode: 'classic',
          collection_accounts_group_by: 'client',
        }),
      };
    }
    if (apiPath === 'accounting/hostings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [hosting],
          meta: { active_count: 1, monthly_income: '91667.00' },
        }),
      };
    }
    if (apiPath === 'accounting/incomes/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [income], meta: {} }),
      };
    }
    if (apiPath === 'accounting/collection-accounts/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [collection],
          meta: {
            issued_count: 1,
            issued_total: '1160000.00',
            paid_count: 0,
            paid_total: '0.00',
            cancelled_count: 0,
          },
        }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function arrangePanel(page, calls, path, heading) {
  await setAuthLocalStorage(page, {
    token: 'e2e-token',
    userAuth: { id: 9001, role: 'admin', is_staff: true },
  });
  await mockApi(page.context(), buildHandler(calls));
  await page.goto(path, { waitUntil: 'domcontentloaded' });
  await waitForNuxtApp(page);
  await expect(page.getByRole('heading', { name: heading, exact: true }))
    .toBeVisible({ timeout: 45_000 });
}

async function openPlatformPopup(page, testId) {
  const popupPromise = page.context().waitForEvent('page');
  await page.getByTestId(testId).filter({ visible: true }).click();
  const popup = await popupPromise;

  await popup.waitForURL(new RegExp(`/platform/projects/${PROJECT_ID}$`), { timeout: 25_000 });
  return popup;
}

test('hosting project reference opens its platform space', {
  tag: [...ADMIN_ACCOUNTING_HOSTINGS, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = [];
  await arrangePanel(page, calls, '/panel/accounting/hostings', 'Hostings');

  const popup = await openPlatformPopup(page, 'hosting-project-space-101');

  await expect(popup).toHaveURL(new RegExp(`/platform/projects/${PROJECT_ID}$`));
  expect(calls).toEqual([{
    apiPath: 'accounts/session-token-bridge/',
    method: 'POST',
  }]);
});

test('income project reference opens its platform space', {
  tag: [...ADMIN_ACCOUNTING_INCOME_CRUD, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = [];
  await arrangePanel(
    page,
    calls,
    '/panel/accounting/incomes?accounting_incomeTab=all',
    'Ingresos',
  );

  const popup = await openPlatformPopup(page, 'income-project-space-201');

  await expect(popup).toHaveURL(new RegExp(`/platform/projects/${PROJECT_ID}$`));
  expect(calls).toEqual([{
    apiPath: 'accounts/session-token-bridge/',
    method: 'POST',
  }]);
});

test('collection project reference opens its platform space', {
  tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:success'],
}, async ({ page }) => {
  const calls = [];
  await arrangePanel(page, calls, '/panel/accounting/collections', 'Cuentas de cobro');

  const popup = await openPlatformPopup(page, 'collection-project-space-301');

  await expect(popup).toHaveURL(new RegExp(`/platform/projects/${PROJECT_ID}$`));
  expect(calls).toEqual([{
    apiPath: 'accounts/session-token-bridge/',
    method: 'POST',
  }]);
});
