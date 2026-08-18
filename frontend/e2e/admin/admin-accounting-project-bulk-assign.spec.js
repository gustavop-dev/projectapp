/**
 * E2E tests for the bulk PROJECT target of the accounting assign bar.
 *
 * FLOWS: admin-accounting-project-bulk-assign
 * Covers: Asignar proyecto reached from the hostings actions menu; the
 *         catalog-wide project picker; the confirmation that names the
 *         foreign-client rows the action refuses to touch (they never
 *         travel); the in-place row update without a reload; the disabled
 *         state until a project is picked; and Quitar proyecto as its own
 *         destructive action.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { bulkAction, bulkMenuItem, openBulkMenu } from '../helpers/bulk-actions.js';
import { ADMIN_ACCOUNTING_PROJECT_BULK_ASSIGN } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function hostingRow(overrides = {}) {
  return {
    id: 1,
    client: 5,
    client_display_name: 'Kore SAS',
    billing_email: '',
    client_name: 'German - Kore',
    project: null,
    project_name: null,
    domain_url: 'https://korehealths.com/',
    monthly_value: '91667.00',
    payment_modality: 'monthly',
    payment_modality_label: 'Mensual',
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
    ...overrides,
  };
}

const ROWS = [
  hostingRow({ id: 1 }),
  hostingRow({
    id: 2,
    client: 9,
    client_display_name: 'Ana Pérez',
    client_name: 'Ana - Otro',
    domain_url: 'https://otro.com/',
  }),
  hostingRow({
    id: 3,
    project: 41,
    project_name: 'Vieja Web',
    domain_url: 'https://vieja.com/',
  }),
];

const CATALOG = [
  {
    id: 40,
    name: 'Kore Web',
    status: 'active',
    status_label: 'Activo',
    client: { profile_id: 5, name: 'Kore SAS', company: '' },
    hostings_count: 0,
    incomes_count: 0,
    unlinked_hostings_count: 2,
    unlinked_incomes_count: 0,
  },
];

const META = {
  active_count: 3,
  monthly_income: '110000.00',
  expiring_soon_count: 0,
  total_paid: '0.00',
  without_client_count: 0,
  without_project_count: 2,
};

/**
 * Stateful on purpose: the page refetches after every mutation
 * (onAfterMutation → loadRecords), so a static list would silently undo
 * the assignment the assertions are about.
 */
function buildHandler({ calls, state }) {
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
        body: JSON.stringify({ results: state.rows, meta: META }),
      };
    }
    if (apiPath === 'projects/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: CATALOG,
          meta: { total: 1, active: 1, archived: 0 },
        }),
      };
    }
    if (apiPath === 'accounting/hostings/bulk-assign-project/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      const target = body.project;
      state.rows = state.rows.map((row) => (
        body.hosting_ids.includes(row.id)
          ? { ...row, project: target, project_name: target ? 'Kore Web' : null }
          : row
      ));
      const updated = state.rows.filter((row) => body.hosting_ids.includes(row.id));
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ updated: updated.length, results: updated }),
      };
    }
    return null;
  };
}

async function gotoHostings(page) {
  await page.goto('/panel/accounting/hostings', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Hostings', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
}

test.describe('Admin Accounting — bulk project assignment', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('assigning confirms the plan, blocks the foreign row, and updates in place', {
    tag: [...ADMIN_ACCOUNTING_PROJECT_BULK_ASSIGN, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, state: { rows: [...ROWS] } }));
    await gotoHostings(page);

    await page.getByTestId('accounting-select-1').check();
    await page.getByTestId('accounting-select-2').check();
    await page.getByTestId('accounting-select-3').check();
    await expect(page.getByTestId('hostings-bulk-bar')).toContainText('3 seleccionados');

    await bulkAction(page, 'hostings', 'Asignar proyecto');
    await page.getByTestId('hostings-bulk-project').click();
    await page.getByTestId('hostings-bulk-project-option-40').click();

    // The mass edit shows its exact scope first: what moves, and what the
    // ownership rule refuses to touch. The plan is live in the modal now, so
    // it is on screen BEFORE the confirm rather than behind it.
    await expect(page.getByTestId('project-bulk-summary-blocked')).toContainText('otro.com');
    await expect(page.getByTestId('project-bulk-summary-list')).toContainText('korehealths.com');
    await expect(page.getByTestId('project-bulk-summary-list')).toContainText('Vieja Web');
    expect(calls).toHaveLength(0);

    await page.getByTestId('hostings-bulk-assign-project').click();

    await expect(page.getByTestId('accounting-row-1')).toContainText('Kore Web');
    await expect(page.getByTestId('hostings-bulk-bar')).toHaveCount(0);
    expect(calls[0].body).toEqual({ hosting_ids: [1, 3], project: 40 });
  });

  test('assigning stays blocked, with the reason on screen, until a project is picked', {
    tag: [...ADMIN_ACCOUNTING_PROJECT_BULK_ASSIGN, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [], state: { rows: [...ROWS] } }));
    await gotoHostings(page);

    await page.getByTestId('accounting-select-1').check();

    // Row 1 has no project, so the menu does not offer to remove one — and the
    // menu has to be OPEN for that absence to mean anything.
    await openBulkMenu(page, 'hostings');
    await expect(bulkMenuItem(page, 'Quitar proyecto')).toHaveCount(0);
    await bulkMenuItem(page, 'Asignar proyecto').click();

    await expect(page.getByTestId('hostings-bulk-assign-project')).toBeDisabled();
    await expect(page.getByTestId('hostings-bulk-hint')).toContainText(
      'Elige un proyecto para poder asignar',
    );
  });

  test('Quitar proyecto is its own destructive action and clears the cell', {
    tag: [...ADMIN_ACCOUNTING_PROJECT_BULK_ASSIGN, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls, state: { rows: [...ROWS] } }));
    await gotoHostings(page);

    await page.getByTestId('accounting-select-3').check();

    await bulkAction(page, 'hostings', 'Quitar proyecto');
    await expect(page.getByRole('dialog')).toContainText(
      '1 hosting quedará sin proyecto: 1 de Vieja Web.',
    );
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByTestId('hosting-no-project-3')).toBeVisible();
    expect(calls[0].body).toEqual({ hosting_ids: [3], project: null });
  });
});
