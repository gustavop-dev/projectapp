/**
 * E2E tests for on-the-fly project creation from the accounting selectors.
 *
 * FLOWS: admin-project-fly-create
 * Covers: creating a project from inside the hosting modal (typed term
 *         pre-filled, auto-selection, the id travelling in the hosting
 *         payload); the 400 that keeps the inline panel open; the income
 *         modal variant; and the persistence of a fly-created project after
 *         cancelling the outer form (it is a record, not a draft).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROJECT_FLY_CREATE } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const CLIENT_SEARCH_RESULT = [{
  id: 5,
  name: 'Germán Franco',
  email: 'german@korehealths.com',
  phone: '',
  company: 'Kore',
  nit: '901234567',
  cedula: '',
  is_email_placeholder: false,
}];

const INCOME_ROW = {
  id: 41,
  concept: 'Hosting Kore semestre',
  kind: 'expected',
  kind_label: 'Esperado',
  period: '2026-08',
  period_label: 'Agosto 2026',
  period_date: '2026-08-01',
  total_amount: '550002.00',
  gustavo_amount: '275001.00',
  carlos_amount: '275001.00',
  company_amount: '0.00',
  client: null,
  client_name: null,
  project: null,
  project_name: null,
  origin: '',
  notes: '',
  created_at: '2026-08-01T10:00:00Z',
  updated_at: '2026-08-01T10:00:00Z',
};

/**
 * Mutable per-run mock state: the fly-created project lands in `projects`
 * so a later fetch of the picker (modal re-open) serves it — the same
 * behavior the real backend has, which is what the persistence test pins.
 */
function buildHandler({ calls, projects, createStatus = 201 }) {
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
    if (apiPath.startsWith('accounting/projects/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: projects }),
      };
    }
    if (apiPath === 'projects/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      if (createStatus !== 201) {
        return {
          status: createStatus,
          contentType: 'application/json',
          body: JSON.stringify({ name: ['Ya no se pudo crear.'] }),
        };
      }
      const row = {
        id: 31,
        name: body.name,
        status: 'active',
        status_label: 'Activo',
        description: '',
        created_at: '2026-08-13T10:00:00Z',
        client: { profile_id: body.client_profile_id, name: 'Germán Franco', company: 'Kore' },
        hostings_count: 0,
        incomes_count: 0,
      };
      projects.push({ id: 31, name: body.name, status: 'active', status_label: 'Activo' });
      return { status: 201, contentType: 'application/json', body: JSON.stringify(row) };
    }
    if (apiPath === 'accounting/hostings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], meta: {} }),
      };
    }
    if (apiPath === 'accounting/hostings/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 99, ...body }),
      };
    }
    if (apiPath === 'accounting/incomes/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [INCOME_ROW], meta: {} }),
      };
    }
    if (apiPath === 'accounting/settings/' && method === 'GET') {
      // The incomes page reads the landing mode on mount; production
      // defaults to grouped, which would break the classic-table flow.
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ income_default_view_mode: 'classic' }),
      };
    }
    if (apiPath.startsWith('proposals/client-profiles/search/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(CLIENT_SEARCH_RESULT),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function openHostingModalWithClient(page) {
  await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Hostings', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
  await page.getByTestId('hostings-new-button').click();
  await page.getByTestId('hosting-form-client').fill('Germán');
  await page.getByTestId('client-autocomplete-option-5').click();
}

test.describe('Admin Project Fly Create', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('creates a project from the hosting modal and the id travels in the payload', {
    tag: [...ADMIN_PROJECT_FLY_CREATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, projects: [] }));
    await openHostingModalWithClient(page);

    await page.getByTestId('hosting-form-project').fill('Kore 2');
    await page.getByTestId('hosting-form-project-create-new').click();
    await expect(
      page.getByTestId('hosting-form-project-inline-name'),
    ).toHaveValue('Kore 2');
    await page.getByTestId('hosting-form-project-inline-create-save').click();

    // Auto-selected: the combobox shows the new project without re-searching.
    await expect(page.getByTestId('hosting-form-project')).toHaveValue('Kore 2');
    expect(calls[0]).toMatchObject({
      apiPath: 'projects/create/',
      body: { name: 'Kore 2', client_profile_id: 5 },
    });

    await page.getByTestId('hosting-form-monthly').fill('91667');
    await page.getByTestId('hosting-form-submit').click();

    const hostingCall = calls.find((c) => c.apiPath === 'accounting/hostings/create/');
    expect(hostingCall.body.project).toBe(31);
  });

  test('a rejected creation keeps the inline panel open with the message', {
    tag: [...ADMIN_PROJECT_FLY_CREATE, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, projects: [], createStatus: 400 }));
    await openHostingModalWithClient(page);

    await page.getByTestId('hosting-form-project').fill('Kore 2');
    await page.getByTestId('hosting-form-project-create-new').click();
    await page.getByTestId('hosting-form-project-inline-create-save').click();

    await expect(
      page.getByTestId('hosting-form-project-inline-create-error'),
    ).toHaveText('Ya no se pudo crear.');
    await expect(page.getByTestId('hosting-form-project-inline-create')).toBeVisible();
    // Nothing was committed: one rejected POST, no selectable new option.
    expect(calls.filter((c) => c.apiPath === 'projects/create/')).toHaveLength(1);
    await expect(page.getByTestId('hosting-form-project-option-31')).toHaveCount(0);
  });

  test('the income modal shares the same selector and flow', {
    tag: [...ADMIN_PROJECT_FLY_CREATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, projects: [] }));
    await page.goto('/panel/accounting/incomes?accounting_incomeTab=all', {
      waitUntil: 'domcontentloaded',
    });
    await expect(
      page.getByRole('heading', { name: 'Ingresos', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('incomes-new-button').click();
    await page.getByTestId('income-form-client').fill('Germán');
    await page.getByTestId('client-autocomplete-option-5').click();

    await page.getByTestId('income-form-project').fill('Crushme');
    await page.getByTestId('income-form-project-create-new').click();
    await page.getByTestId('income-form-project-inline-create-save').click();

    await expect(page.getByTestId('income-form-project')).toHaveValue('Crushme');
    expect(calls[0]).toMatchObject({
      apiPath: 'projects/create/',
      body: { name: 'Crushme', client_profile_id: 5 },
    });
  });

  test('cancelling the outer form leaves the fly-created project standing', {
    tag: [...ADMIN_PROJECT_FLY_CREATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    const projects = [];
    await mockApi(page, buildHandler({ calls, projects }));
    await openHostingModalWithClient(page);

    await page.getByTestId('hosting-form-project').fill('Kore 2');
    await page.getByTestId('hosting-form-project-create-new').click();
    await page.getByTestId('hosting-form-project-inline-create-save').click();
    await expect(page.getByTestId('hosting-form-project')).toHaveValue('Kore 2');

    // Abandon the hosting form AFTER the project was created.
    await page.getByRole('button', { name: 'Cancelar', exact: true }).click();
    expect(calls.filter((c) => c.apiPath === 'projects/create/')).toHaveLength(1);

    // Re-open: the picker lists the project — it exists server-side, no
    // draft died with the cancelled form.
    await page.getByTestId('hostings-new-button').click();
    await page.getByTestId('hosting-form-client').fill('Germán');
    await page.getByTestId('client-autocomplete-option-5').click();
    await page.getByTestId('hosting-form-project').click();
    await expect(page.getByTestId('hosting-form-project-option-31')).toContainText('Kore 2');
  });
});
