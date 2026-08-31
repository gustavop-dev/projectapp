/**
 * E2E tests for the "Archivados" tab in the admin clients page.
 *
 * Covers: the Archivados tab requesting archived=true and rendering only
 * archived clients, and the row toggle PATCHing is_archived.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENT_ARCHIVED_TAB } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const activeClient = {
  id: 101,
  name: 'Carlos López',
  email: 'carlos@test.com',
  phone: '+57 300 123 4567',
  company: 'Carlos Corp',
  is_onboarded: true,
  is_email_placeholder: false,
  total_proposals: 3,
  is_orphan: false,
  is_archived: false,
  archived_at: null,
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-03-10T10:00:00Z',
};

const archivedClient = {
  id: 104,
  name: 'Dora Dormida',
  email: 'dora@test.com',
  phone: '',
  company: 'Dora SAS',
  is_onboarded: false,
  is_email_placeholder: false,
  total_proposals: 1,
  is_orphan: false,
  is_archived: true,
  archived_at: '2026-06-01T10:00:00Z',
  created_at: '2026-02-01T10:00:00Z',
  updated_at: '2026-06-01T10:00:00Z',
};

function setupMock(page, { onUpdate = null } = {}) {
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath === 'proposals/client-profiles/status-counts/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ all: 1, active: 1, orphans: 0, archived: 1 }),
      };
    }

    if (apiPath === 'proposals/client-profiles/') {
      const requestUrl = new URL(route.request().url());
      const archivedParam = requestUrl.searchParams.get('archived');
      const filtered = archivedParam === 'true' ? [archivedClient] : [activeClient];
      return { status: 200, contentType: 'application/json', body: JSON.stringify(filtered) };
    }

    const updateMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/update\/$/);
    if (updateMatch && method === 'PATCH') {
      const clientId = Number(updateMatch[1]);
      const body = JSON.parse(route.request().postData() || '{}');
      if (onUpdate) onUpdate(clientId, body);
      const source = clientId === archivedClient.id ? archivedClient : activeClient;
      const updated = {
        ...source,
        is_archived: Boolean(body.is_archived),
        archived_at: body.is_archived ? '2026-07-09T10:00:00Z' : null,
      };
      return { status: 200, contentType: 'application/json', body: JSON.stringify(updated) };
    }

    return null;
  });
}

async function gotoClients(page) {
  await page.goto('/panel/clients');
  await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 30_000 });
}

test.describe('Admin Clients Archived Tab', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('Archivados requests archived=true and lists only archived clients', {
    tag: [...ADMIN_CLIENT_ARCHIVED_TAB, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (reaching /panel/clients through the sidebar is
    // its own flow; the status selector is the subject here)
    await setupMock(page);
    await gotoClients(page);

    // Default status hides the archived client.
    await expect(page.getByText('Carlos López')).toBeVisible();
    await expect(page.getByText('Dora Dormida')).not.toBeVisible();

    // Status is a transversal selector next to the search box now, labelled
    // with its own match count.
    const archivedRequest = page.waitForRequest((req) => req.url().includes('archived=true'));
    await page.getByTestId('clients-status-archived').click();
    await archivedRequest;

    await expect(page.getByText('Dora Dormida')).toBeVisible();
    await expect(page.getByText('Carlos López')).not.toBeVisible();
    await expect(page.getByText('Archivado', { exact: true })).toBeVisible();
    await expect(page).toHaveURL(/status=archived/);
  });

  test('the row toggle PATCHes is_archived=true and notifies', {
    tag: [...ADMIN_CLIENT_ARCHIVED_TAB, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onUpdate: (clientId, body) => updates.push({ clientId, body }) });
    await gotoClients(page);

    await expect(page.getByText('Carlos López')).toBeVisible();
    await page.getByTestId('client-toggle-archived-101').click();

    await expect(page.getByText('"Carlos López" marcado como inactivo.')).toBeVisible();
    expect(updates).toEqual([{ clientId: 101, body: { is_archived: true } }]);
  });

  test('the toggle from the Archivados list brings the client back', {
    tag: [...ADMIN_CLIENT_ARCHIVED_TAB, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onUpdate: (clientId, body) => updates.push({ clientId, body }) });
    await gotoClients(page);

    const archivedRequest = page.waitForRequest((req) => req.url().includes('archived=true'));
    await page.getByTestId('clients-status-archived').click();
    await archivedRequest;
    await expect(page.getByText('Dora Dormida')).toBeVisible();

    await page.getByTestId('client-toggle-archived-104').click();

    await expect(page.getByText('"Dora Dormida" reactivado.')).toBeVisible();
    expect(updates).toEqual([{ clientId: 104, body: { is_archived: false } }]);
  });
});

