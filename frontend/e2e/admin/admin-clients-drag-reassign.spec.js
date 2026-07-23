/**
 * E2E tests for drag-and-drop reassignment in the admin clients page.
 *
 * Covers: dragging a proposal/diagnostic row from an expanded client onto
 * another client card header OR its matching proposals/diagnostics zone
 * PATCHes client_id; dropping on the source client or on a zone of the
 * other type is a no-op. Native DnD is simulated with a shared DataTransfer
 * handle + dispatchEvent (Playwright's dragAndDrop is unreliable with
 * custom handlers).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENT_DRAG_REASSIGN } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockClients = [
  {
    id: 101,
    name: 'Carlos López',
    email: 'carlos@test.com',
    phone: '',
    company: 'Carlos Corp',
    is_onboarded: true,
    is_email_placeholder: false,
    total_proposals: 1,
    is_orphan: false,
    is_inactive: false,
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-03-10T10:00:00Z',
  },
  {
    id: 102,
    name: 'Ana Martínez',
    email: 'ana@test.com',
    phone: '',
    company: 'Ana Studio',
    is_onboarded: false,
    is_email_placeholder: false,
    total_proposals: 0,
    is_orphan: false,
    is_inactive: false,
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-03-12T10:00:00Z',
  },
];

const mockClientDetails = {
  101: {
    ...mockClients[0],
    proposals: [
      {
        id: 1,
        title: 'Propuesta Alpha',
        status: 'sent',
        available_transitions: ['negotiating', 'rejected'],
        total_investment: 5000000,
        currency: 'COP',
        view_count: 5,
        sent_at: '2026-01-10T10:00:00Z',
      },
    ],
    projects: [],
    diagnostics: [
      {
        id: 5,
        title: 'Diagnóstico Web Carlos',
        status: 'draft',
        created_at: '2026-02-15T10:00:00Z',
      },
    ],
  },
  102: {
    ...mockClients[1],
    proposals: [],
    projects: [],
    diagnostics: [
      {
        id: 6,
        title: 'Diagnóstico Web Ana',
        status: 'draft',
        created_at: '2026-03-01T10:00:00Z',
      },
    ],
  },
};

function setupMock(page, { onProposalUpdate = null, onDiagnosticUpdate = null } = {}) {
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath === 'proposals/client-profiles/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockClients) };
    }

    const detailMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/$/);
    if (detailMatch) {
      const clientId = Number(detailMatch[1]);
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockClientDetails[clientId] || { ...mockClients[0], proposals: [], projects: [], diagnostics: [] }),
      };
    }

    const proposalMatch = apiPath.match(/^proposals\/(\d+)\/update\/$/);
    if (proposalMatch && method === 'PATCH') {
      const body = JSON.parse(route.request().postData() || '{}');
      if (onProposalUpdate) onProposalUpdate(Number(proposalMatch[1]), body);
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...mockClientDetails[101].proposals[0], client_id: body.client_id }),
      };
    }

    const diagnosticMatch = apiPath.match(/^diagnostics\/(\d+)\/update\/$/);
    if (diagnosticMatch && method === 'PATCH') {
      const body = JSON.parse(route.request().postData() || '{}');
      if (onDiagnosticUpdate) onDiagnosticUpdate(Number(diagnosticMatch[1]), body);
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...mockClientDetails[101].diagnostics[0], client_id: body.client_id }),
      };
    }

    return null;
  });
}

async function gotoClientsAndExpandCarlos(page) {
  await page.goto('/panel/clients');
  await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 30_000 });
  await page.getByTestId('client-header-101').click();
  await expect(page.getByTestId('client-proposal-row-1')).toBeVisible();
}

async function dragRowTo(page, rowTestId, targetTestId) {
  const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
  await page.getByTestId(rowTestId).dispatchEvent('dragstart', { dataTransfer });
  await page.getByTestId(targetTestId).dispatchEvent('dragover', { dataTransfer });
  await page.getByTestId(targetTestId).dispatchEvent('drop', { dataTransfer });
  await page.getByTestId(rowTestId).dispatchEvent('dragend', { dataTransfer }).catch(() => {});
}

test.describe('Admin Clients Drag Reassign', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('dropping a proposal on another client PATCHes client_id and notifies', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onProposalUpdate: (id, body) => updates.push({ id, body }) });
    await gotoClientsAndExpandCarlos(page);

    await dragRowTo(page, 'client-proposal-row-1', 'client-header-102');

    await expect(page.getByText('"Propuesta Alpha" movido a Ana Martínez.')).toBeVisible();
    expect(updates).toEqual([{ id: 1, body: { client_id: 102 } }]);
  });

  test('dropping a proposal on another client proposals zone PATCHes client_id', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onProposalUpdate: (id, body) => updates.push({ id, body }) });
    await gotoClientsAndExpandCarlos(page);
    await page.getByTestId('client-header-102').click();
    await expect(page.getByTestId('client-proposals-zone-102')).toBeVisible();

    await dragRowTo(page, 'client-proposal-row-1', 'client-proposals-zone-102');

    await expect(page.getByText('"Propuesta Alpha" movido a Ana Martínez.')).toBeVisible();
    expect(updates).toEqual([{ id: 1, body: { client_id: 102 } }]);
  });

  test('dropping a diagnostic on another client diagnostics zone PATCHes client_id', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onDiagnosticUpdate: (id, body) => updates.push({ id, body }) });
    await gotoClientsAndExpandCarlos(page);
    await page.getByTestId('client-header-102').click();
    await expect(page.getByTestId('client-diagnostics-zone-102')).toBeVisible();

    await dragRowTo(page, 'client-diagnostic-row-5', 'client-diagnostics-zone-102');

    await expect(page.getByText('"Diagnóstico Web Carlos" movido a Ana Martínez.')).toBeVisible();
    expect(updates).toEqual([{ id: 5, body: { client_id: 102 } }]);
  });

  test('dropping a diagnostic on a proposals zone issues no PATCH', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, {
      onProposalUpdate: (id, body) => updates.push({ id, body }),
      onDiagnosticUpdate: (id, body) => updates.push({ id, body }),
    });
    await gotoClientsAndExpandCarlos(page);
    await page.getByTestId('client-header-102').click();
    await expect(page.getByTestId('client-proposals-zone-102')).toBeVisible();

    await dragRowTo(page, 'client-diagnostic-row-5', 'client-proposals-zone-102');

    await expect(page.getByText('movido a')).not.toBeVisible();
    expect(updates).toEqual([]);
  });

  test('dropping a diagnostic on another client PATCHes client_id', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onDiagnosticUpdate: (id, body) => updates.push({ id, body }) });
    await gotoClientsAndExpandCarlos(page);
    await expect(page.getByTestId('client-diagnostic-row-5')).toBeVisible();

    await dragRowTo(page, 'client-diagnostic-row-5', 'client-header-102');

    await expect(page.getByText('"Diagnóstico Web Carlos" movido a Ana Martínez.')).toBeVisible();
    expect(updates).toEqual([{ id: 5, body: { client_id: 102 } }]);
  });

  test('dropping on the source client issues no PATCH', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, {
      onProposalUpdate: (id, body) => updates.push({ id, body }),
      onDiagnosticUpdate: (id, body) => updates.push({ id, body }),
    });
    await gotoClientsAndExpandCarlos(page);

    await dragRowTo(page, 'client-proposal-row-1', 'client-header-101');

    await expect(page.getByText('movido a')).not.toBeVisible();
    expect(updates).toEqual([]);
  });

  test('the Deshacer action on the toast reassigns the item back', {
    tag: [...ADMIN_CLIENT_DRAG_REASSIGN, '@role:admin'],
  }, async ({ page }) => {
    const updates = [];
    await setupMock(page, { onProposalUpdate: (id, body) => updates.push({ id, body }) });
    await gotoClientsAndExpandCarlos(page);

    await dragRowTo(page, 'client-proposal-row-1', 'client-header-102');
    await expect(page.getByText('"Propuesta Alpha" movido a Ana Martínez.')).toBeVisible();

    await page.getByRole('button', { name: 'Deshacer' }).click();

    await expect(page.getByText('"Propuesta Alpha" movido a Carlos López.')).toBeVisible();
    expect(updates).toEqual([
      { id: 1, body: { client_id: 102 } },
      { id: 1, body: { client_id: 101 } },
    ]);
  });
});

