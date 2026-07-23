/**
 * E2E tests for the "Inactivos" tab in the admin clients page.
 *
 * Covers: the Inactivos tab requesting inactive=true and rendering only
 * deactivated clients, and the pause/play toggle PATCHing is_inactive.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENT_INACTIVE_TAB } from '../helpers/flow-tags.js';

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
  is_inactive: false,
  deactivated_at: null,
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-03-10T10:00:00Z',
};

const inactiveClient = {
  id: 104,
  name: 'Dora Dormida',
  email: 'dora@test.com',
  phone: '',
  company: 'Dora SAS',
  is_onboarded: false,
  is_email_placeholder: false,
  total_proposals: 1,
  is_orphan: false,
  is_inactive: true,
  deactivated_at: '2026-06-01T10:00:00Z',
  created_at: '2026-02-01T10:00:00Z',
  updated_at: '2026-06-01T10:00:00Z',
};

function setupMock(page, { onUpdate = null } = {}) {
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath === 'proposals/client-profiles/') {
      const requestUrl = new URL(route.request().url());
      const inactiveParam = requestUrl.searchParams.get('inactive');
      const filtered = inactiveParam === 'true' ? [inactiveClient] : [activeClient];
      return { status: 200, contentType: 'application/json', body: JSON.stringify(filtered) };
    }

    const updateMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/update\/$/);
    if (updateMatch && method === 'PATCH') {
      const clientId = Number(updateMatch[1]);
      const body = JSON.parse(route.request().postData() || '{}');
      if (onUpdate) onUpdate(clientId, body);
      const source = clientId === inactiveClient.id ? inactiveClient : activeClient;
      const updated = {
        ...source,
        is_inactive: Boolean(body.is_inactive),
        deactivated_at: body.is_inactive ? '2026-07-09T10:00:00Z' : null,
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

test.describe('Admin Clients Inactive Tab', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('Inactivos tab requests inactive=true and lists only deactivated clients', {
    tag: [...ADMIN_CLIENT_INACTIVE_TAB, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    // Default tab hides the inactive client.
    await expect(page.getByText('Carlos López')).toBeVisible();
    await expect(page.getByText('Dora Dormida')).not.toBeVisible();

    const inactiveRequest = page.waitForRequest((req) => req.url().includes('inactive=true'));
    await page.getByTestId('clients-tab-inactive').click();
    await inactiveRequest;

    await expect(page.getByText('Dora Dormida')).toBeVisible();
    await expect(page.getByText('Carlos López')).not.toBeVisible();
    await expect(page.getByText('Inactivo', { exact: true })).toBeVisible();
  });

  test('pause toggle PATCHes is_inactive=true and notifies', {
    tag: [...ADMIN_CLIENT_INACTIVE_TAB, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onUpdate: (clientId, body) => updates.push({ clientId, body }) });
    await gotoClients(page);

    await expect(page.getByText('Carlos López')).toBeVisible();
    await page.getByTestId('client-toggle-inactive-101').click();

    await expect(page.getByText('"Carlos López" marcado como inactivo.')).toBeVisible();
    expect(updates).toEqual([{ clientId: 101, body: { is_inactive: true } }]);
  });

  test('play toggle from the Inactivos tab reactivates the client', {
    tag: [...ADMIN_CLIENT_INACTIVE_TAB, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onUpdate: (clientId, body) => updates.push({ clientId, body }) });
    await gotoClients(page);

    const inactiveRequest = page.waitForRequest((req) => req.url().includes('inactive=true'));
    await page.getByTestId('clients-tab-inactive').click();
    await inactiveRequest;
    await expect(page.getByText('Dora Dormida')).toBeVisible();

    await page.getByTestId('client-toggle-inactive-104').click();

    await expect(page.getByText('"Dora Dormida" reactivado.')).toBeVisible();
    expect(updates).toEqual([{ clientId: 104, body: { is_inactive: false } }]);
  });
});

