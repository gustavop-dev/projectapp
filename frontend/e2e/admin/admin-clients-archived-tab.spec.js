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

function setupMock(page, { onUpdate = null, archiveStatus = 200 } = {}) {
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

    // Archiving never goes through the identity PATCH: it suspends the
    // client's projects, so it has its own preview + apply pair.
    const previewMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/archive-preview\/$/);
    if (previewMatch) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          client_id: Number(previewMatch[1]),
          client_name: 'Carlos López',
          target_state_id: 4,
          target_state_name: 'Suspendido',
          projects: [{
            project_id: 7,
            project_name: 'Portal Carlos',
            current_state: 'Activo',
            impact_token: 'tok-7',
            future_incomes: [{ id: 1, concept: 'Hosting' }],
            future_payments: [],
            active_hostings: [],
            blockers: [],
          }],
          skipped: [],
          totals: { future_incomes: 1, future_payments: 0, active_hostings: 0 },
        }),
      };
    }

    const archiveMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/(archive|unarchive)\/$/);
    if (archiveMatch && method === 'POST') {
      if (archiveStatus === 409) {
        return {
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'projects_changed',
            message: 'La lista de proyectos cambió desde la vista previa. Revísala de nuevo.',
          }),
        };
      }
      const clientId = Number(archiveMatch[1]);
      const archiving = archiveMatch[2] === 'archive';
      const body = JSON.parse(route.request().postData() || '{}');
      if (onUpdate) onUpdate(clientId, { archiving, ...body });
      const source = clientId === archivedClient.id ? archivedClient : activeClient;
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          client: {
            ...source,
            is_archived: archiving,
            archived_at: archiving ? '2026-07-09T10:00:00Z' : null,
          },
          suspended_projects: archiving ? [7] : [],
          still_suspended: archiving ? [] : [7],
        }),
      };
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

  test('the row toggle previews the cascade before archiving', {
    tag: [...ADMIN_CLIENT_ARCHIVED_TAB, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onUpdate: (clientId, body) => updates.push({ clientId, body }) });
    await gotoClients(page);

    await expect(page.getByText('Carlos López')).toBeVisible();
    const archiveToggle = page.getByTestId('client-toggle-archived-101');
    await archiveToggle.hover();
    await expect(page.getByRole('tooltip')).toHaveText('Archivar');
    await archiveToggle.click();

    // The warning has to name the cost before the confirm turns on: suspending
    // the project cancels its future income and nothing brings it back.
    const impact = page.getByTestId('client-archive-impact');
    await expect(impact).toContainText('1 proyecto pasará a «Suspendido»');
    await expect(impact).toContainText('Portal Carlos');
    await expect(impact).toContainText('1 ingresos futuros se marcarán como cancelados.');
    await expect(impact).toContainText('Reactivar después no revierte esas cancelaciones.');

    await page.getByTestId('client-archive-confirm').click();

    await expect(page.getByText('"Carlos López" archivado.')).toBeVisible();
    expect(updates).toEqual([{
      clientId: 101,
      body: {
        archiving: true,
        transitions: [{ project_id: 7, impact_token: 'tok-7' }],
      },
    }]);
  });

  test('a confirmation that went stale is refused, not applied', {
    tag: [...ADMIN_CLIENT_ARCHIVED_TAB, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupMock(page, { archiveStatus: 409 });
    await gotoClients(page);

    await expect(page.getByText('Carlos López')).toBeVisible();
    await page.getByTestId('client-toggle-archived-101').click();
    await expect(page.getByTestId('client-archive-impact')).toBeVisible();

    await page.getByTestId('client-archive-confirm').click();

    // The modal stays open with the reason. Applying anyway would suspend a
    // project — and cancel its income — under a confirmation for a different
    // set of projects than the one on screen.
    await expect(page.getByTestId('client-archive-error'))
      .toContainText('La lista de proyectos cambió desde la vista previa.');
    await expect(page.getByTestId('client-archive-modal')).toBeVisible();
    await expect(page.getByText('"Carlos López" archivado.')).toHaveCount(0);
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

    const unarchiveToggle = page.getByTestId('client-toggle-archived-104');
    await unarchiveToggle.hover();
    await expect(page.getByRole('tooltip')).toHaveText('Desarchivar');
    await unarchiveToggle.click();

    // Unarchiving says out loud that the projects stay suspended: their
    // cancelled incomes do not come back, so reactivating is a separate call.
    await expect(page.getByTestId('client-archive-unarchive-note'))
      .toContainText('Sus proyectos siguen suspendidos');

    await page.getByTestId('client-archive-confirm').click();

    await expect(page.getByText('"Dora Dormida" desarchivado.')).toBeVisible();
    expect(updates).toEqual([{ clientId: 104, body: { archiving: false } }]);
  });
});
