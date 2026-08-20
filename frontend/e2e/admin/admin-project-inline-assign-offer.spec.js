/**
 * E2E test for the post-create assign offer on the accounting pages: the
 * exact gap the Vástago case exposed.
 *
 * FLOWS: admin-project-inline-assign-offer
 * Covers: creating a project inline from the hosting form's picker, closing
 *         the form (even without saving — the project is a record of its
 *         own), the PA-51 assign modal opening on its own with the client's
 *         backlog, and the confirmed assignment filling the Proyecto cells
 *         without a reload — the response rows rebuild the table.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROJECT_INLINE_ASSIGN_OFFER } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const HOSTING_ROW = {
  id: 21,
  client: 5,
  client_display_name: 'Germán Franco',
  billing_email: '',
  client_name: 'German - Kore',
  project: null,
  project_name: null,
  domain_url: 'https://korehealths.com/',
  monthly_value: '91667.00',
  payment_modality: 'monthly',
  payment_modality_label: 'Mensual (histórico)',
  benefit: '',
  valid_from: '2026-03-02',
  valid_to: '2026-09-02',
  cycles_count: 1,
  payment_per_cycle: '91667.00',
  total_paid: '91667.00',
  is_active: true,
  notes: '',
  created_at: '2026-03-02T10:00:00Z',
  updated_at: '2026-03-02T10:00:00Z',
};

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

function annotatedProject(overrides = {}) {
  return {
    id: 40,
    name: 'Kore Web',
    description: '',
    status: 'active',
    status_label: 'Activo',
    created_at: '2026-08-16T10:00:00Z',
    client: { profile_id: 5, name: 'Germán Franco', company: 'Kore' },
    hostings_count: 0,
    incomes_count: 0,
    unlinked_hostings_count: 1,
    unlinked_incomes_count: 0,
    unlinked_documents_count: 1,
    ...overrides,
  };
}

function buildHandler({ state, calls }) {
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
          results: [state.hosting],
          meta: {
            active_count: 1,
            monthly_income: '91667.00',
            expiring_soon_count: 0,
            total_paid: '91667.00',
            without_client_count: 0,
            without_project_count: state.hosting.project ? 0 : 1,
          },
        }),
      };
    }
    if (apiPath === 'accounting/projects/' && method === 'GET') {
      // The per-client picker: empty until the inline create runs.
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [] }),
      };
    }
    if (apiPath === 'projects/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(annotatedProject({ name: body.name })),
      };
    }
    if (apiPath === 'projects/40/unlinked-records/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          client: { profile_id: 5, name: 'Germán Franco' },
          hostings: [{ id: 21, label: 'Germán Franco — korehealths.com' }],
          incomes: [],
          // The client's documents ride in the same offer (F7) — the issued
          // cuenta is identified by its number, the fill-not-edit case.
          documents: [{
            id: 33,
            label: 'CC Kore',
            type_label: 'Cuenta de cobro',
            number: 'PA-KORE-001',
          }],
          total: 2,
        }),
      };
    }
    if (apiPath === 'projects/40/assign-unlinked/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      state.hosting = { ...state.hosting, project: 40, project_name: 'Kore Web' };
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          assigned_hostings: 1,
          assigned_incomes: 0,
          assigned_documents: 1,
          hostings: [state.hosting],
          incomes: [],
          documents: [{ id: 33, project: 40, project_name: 'Kore Web' }],
          project: annotatedProject({
            hostings_count: 1,
            unlinked_hostings_count: 0,
            unlinked_documents_count: 0,
          }),
        }),
      };
    }
    if (apiPath === 'projects/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [annotatedProject()],
          meta: {
            total: 1, active: 1, archived: 0,
            clients_without_projects: 0, records_without_project: 1,
          },
        }),
      };
    }
    if (apiPath.startsWith('proposals/client-profiles/search/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(CLIENT_SEARCH_RESULT),
      };
    }
    return null;
  };
}

test.describe('Admin Projects — inline create offers the client backlog', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('creating a project from the hosting form offers and applies the backlog', {
    tag: [...ADMIN_PROJECT_INLINE_ASSIGN_OFFER, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const state = { hosting: { ...HOSTING_ROW } };
    const calls = [];
    await mockApi(page, buildHandler({ state, calls }));

    await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Hostings', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('hosting-no-project-21')).toBeVisible();

    // Inline create from the form's picker (crear al vuelo).
    await page.getByTestId('hostings-new-button').click();
    await page.getByTestId('hosting-form-client').fill('Germán');
    await page.getByTestId('client-autocomplete-option-5').click();
    await page.getByTestId('hosting-form-project').click();
    await page.getByTestId('hosting-form-project-create-new').click();
    await page.getByTestId('hosting-form-project-inline-name').fill('Kore Web');
    await page.getByTestId('hosting-form-project-inline-create-save').click();
    await expect(page.getByTestId('hosting-form-project')).toHaveValue('Kore Web');

    // Cancelling the form does not cancel the project — and the offer for
    // the client's pre-existing records opens right after it closes.
    await page.getByRole('button', { name: 'Cancelar', exact: true }).click();
    await expect(page.getByTestId('project-assign-unlinked-modal')).toBeVisible();
    await expect(page.getByTestId('project-assign-unlinked-hosting-21')).toBeVisible();
    // The client's documents ride in the same offer (F7), cuentas by number.
    const cuentaRow = page.getByTestId('project-assign-unlinked-document-33');
    await expect(cuentaRow).toContainText('PA-KORE-001');

    await page.getByTestId('project-assign-unlinked-confirm').click();

    // The Proyecto cell fills without any reload: the response rows rebuilt
    // the table the operator is looking at.
    await expect(page.getByTestId('accounting-row-21')).toContainText('Kore Web');
    await expect(page.getByTestId('hosting-no-project-21')).toHaveCount(0);
    const assign = calls.find((c) => c.apiPath === 'projects/40/assign-unlinked/');
    expect(assign.body).toEqual({
      hosting_ids: [21],
      income_ids: [],
      document_ids: [33],
    });
  });
});
