/**
 * FLOW: admin-clients-filter-presets
 *
 * E2E for the predefined one-click filters in /panel/clients: the preset tabs
 * carry a match count before being applied, narrow the list on click, toggle
 * back off, survive a reload through ?clientTab=, combine with the server-side
 * search box, and hand off to Hostings already filtered by the client.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENTS_FILTER_PRESETS } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({
    user: { username: 'admin', is_staff: true, is_superuser: true },
  }),
};

function client(overrides) {
  return {
    email: 'cliente@test.com',
    phone: '',
    company: '',
    is_onboarded: true,
    is_email_placeholder: false,
    total_proposals: 1,
    projects_count: 0,
    diagnostics_count: 0,
    incomes_count: 0,
    hostings_count: 0,
    active_hostings_count: 0,
    active_projects_count: 0,
    is_orphan: false,
    is_inactive: false,
    deactivated_at: null,
    accepted_count: 0,
    last_status: 'sent',
    last_sent_at: '2026-05-01T10:00:00Z',
    project_types: [],
    market_types: [],
    nit: '900123456',
    cedula: '',
    billing_code: 'ACME',
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-05-01T10:00:00Z',
    ...overrides,
  };
}

// Two clients pay hosting today, a third only has an expired one, a fourth
// none at all — so "cobrado" (2) and "histórico" (3) are visibly different.
const CHARGED_ONE = client({
  id: 101, name: 'Kore Healths', company: 'Kore',
  hostings_count: 2, active_hostings_count: 1,
});
const CHARGED_TWO = client({
  id: 102, name: 'Mimittos SAS', company: 'Mimittos',
  hostings_count: 1, active_hostings_count: 1,
});
const EXPIRED_ONLY = client({
  id: 103, name: 'Senses Candles', company: 'Senses',
  hostings_count: 1, active_hostings_count: 0,
});
const NO_HOSTING = client({ id: 104, name: 'Vastago Studio', company: 'Vastago' });

const ALL_CLIENTS = [CHARGED_ONE, CHARGED_TWO, EXPIRED_ONLY, NO_HOSTING];

const HOSTING_ROW = {
  id: 9001,
  client: 101,
  client_name: 'Kore Healths - Kore',
  client_display_name: 'Kore Healths',
  project: null,
  project_name: '',
  domain_url: 'https://korehealths.com/',
  monthly_value: '91667.00',
  payment_modality: 'semiannual',
  payment_modality_label: 'Semestral',
  valid_from: '2026-01-20',
  valid_to: '2026-07-20',
  is_active: true,
  total_paid: '550002.00',
  cycles_count: 1,
  billing_email: 'kore@test.com',
  billing_requested_at: null,
  notes: '',
};

function setupMock(page) {
  return mockApi(page, async ({ route, apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }

    if (apiPath === 'proposals/client-profiles/') {
      const search = (new URL(route.request().url())
        .searchParams.get('search') || '').toLowerCase();
      const rows = search
        ? ALL_CLIENTS.filter((c) => c.name.toLowerCase().includes(search))
        : ALL_CLIENTS;
      return { status: 200, contentType: 'application/json', body: JSON.stringify(rows) };
    }

    if (apiPath === 'accounting/hostings/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [HOSTING_ROW], meta: {} }),
      };
    }

    if (apiPath.startsWith('accounting/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], meta: {} }),
      };
    }

    return null;
  });
}

async function gotoClients(page) {
  await page.goto('/panel/clients');
  await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 30_000 });
}

const rowsShown = (page) => page.locator('[data-testid^="client-row-"]');

test.describe('Admin Clients Filter Presets', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true, is_superuser: true },
    });
  });

  test('the count each preset advertises is the list it actually leaves', {
    tag: [...ADMIN_CLIENTS_FILTER_PRESETS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (reaching /panel/clients through the sidebar is
    // its own flow and is baselined the same way across every clients spec;
    // these tests start from the list because the filter bar is the subject)
    await setupMock(page);
    await gotoClients(page);

    // Readable with the full list still on screen, before applying anything.
    await expect(rowsShown(page)).toHaveCount(4);
    await expect(page.getByTestId('filter-tabs-count-hosting-charged')).toHaveText('2');
    await expect(page.getByTestId('filter-tabs-count-hosting-any')).toHaveText('3');
    await expect(page.getByTestId('filter-tabs-count-active-project')).toHaveText('0');

    // And the advertised number is honest: applying it leaves exactly that many.
    await page.getByTestId('filter-tabs-tab-hosting-any').click();
    await expect(rowsShown(page)).toHaveCount(3);
    await expect(page.getByTestId('filter-tabs-count-hosting-any')).toHaveText('3');
  });

  test('applying the hosting preset narrows the list and stamps the URL', {
    tag: [...ADMIN_CLIENTS_FILTER_PRESETS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    await page.getByTestId('filter-tabs-tab-hosting-charged').click();

    await expect(rowsShown(page)).toHaveCount(2);
    await expect(page.getByText('Kore Healths')).toBeVisible();
    await expect(page.getByText('Senses Candles')).not.toBeVisible();
    await expect(page).toHaveURL(/clientTab=hosting-charged/);
  });

  test('pressing the applied preset again restores the full list', {
    tag: [...ADMIN_CLIENTS_FILTER_PRESETS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    await page.getByTestId('filter-tabs-tab-hosting-charged').click();
    await expect(rowsShown(page)).toHaveCount(2);

    await page.getByTestId('filter-tabs-tab-hosting-charged').click();

    await expect(rowsShown(page)).toHaveCount(4);
    await expect(page.getByText('Vastago Studio')).toBeVisible();
    await expect(page).not.toHaveURL(/clientTab=/);
  });

  test('the shared link reopens the list already filtered', {
    tag: [...ADMIN_CLIENTS_FILTER_PRESETS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the shareable URL is itself the feature under
    // test; reaching the view by clicking would exercise the click path, which
    // the sibling tests already cover)
    // quality: allow-no-interaction (the contract is that the filter is
    // restored before the user touches anything — interacting first would mask
    // a broken restore)
    await setupMock(page);
    await page.goto('/panel/clients?clientTab=hosting-any');
    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 30_000 });

    await expect(rowsShown(page)).toHaveCount(3);
    await expect(page.getByText('Kore Healths')).toBeVisible();
    await expect(page.getByText('Vastago Studio')).not.toBeVisible();
  });

  test('search narrows the preset instead of cancelling it', {
    tag: [...ADMIN_CLIENTS_FILTER_PRESETS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    await page.getByTestId('filter-tabs-tab-hosting-charged').click();
    await expect(rowsShown(page)).toHaveCount(2);

    const searched = page.waitForRequest((req) => req.url().includes('search=Mimittos'));
    await page.getByTestId('clients-search-input').fill('Mimittos');
    await searched;

    // The preset is still on: only the searched client that also pays hosting.
    await expect(rowsShown(page)).toHaveCount(1);
    await expect(page.getByText('Mimittos SAS')).toBeVisible();
    await expect(page).toHaveURL(/clientTab=hosting-charged/);
  });

  test('the row count opens Hostings already filtered by that client', {
    tag: [...ADMIN_CLIENTS_FILTER_PRESETS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    // The hosting count only appears once a hosting preset is applied.
    await expect(page.getByTestId('client-hostings-101')).toHaveCount(0);
    await page.getByTestId('filter-tabs-tab-hosting-charged').click();
    await expect(page.getByTestId('client-hostings-101')).toHaveText('2 hostings');

    await page.getByTestId('client-hostings-101').click();

    await expect(page).toHaveURL(/\/panel\/accounting\/hostings\?client=101/);
    // Landed on Hostings with that client's row in view and the client filter
    // already seeded (one chip, not the unfiltered list).
    await expect(page.getByRole('link', { name: 'https://korehealths.com/' }))
      .toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('accounting-filter-chip')).toHaveCount(1);
  });
});
