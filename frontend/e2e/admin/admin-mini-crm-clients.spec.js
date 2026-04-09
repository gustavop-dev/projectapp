/**
 * E2E tests for admin mini CRM clients page.
 *
 * Covers: client list rendering, search filtering, expanding client
 * to see proposals, and empty state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_MINI_CRM_CLIENTS,
  ADMIN_CLIENT_CREATE_STANDALONE,
  ADMIN_CLIENT_DELETE_ORPHAN,
  ADMIN_CLIENT_DELETE_PROTECTED,
} from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockClients = [
  {
    id: 101,
    name: 'Carlos López',
    email: 'carlos@test.com',
    phone: '+57 300 123 4567',
    company: 'Carlos Corp',
    is_onboarded: true,
    is_email_placeholder: false,
    total_proposals: 3,
    is_orphan: false,
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
    total_proposals: 1,
    is_orphan: false,
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-03-12T10:00:00Z',
  },
];

const mockOrphanClient = {
  id: 103,
  name: 'Pedro Sin Propuestas',
  email: 'pedro@orphan.com',
  phone: '',
  company: '',
  is_onboarded: false,
  is_email_placeholder: false,
  total_proposals: 0,
  is_orphan: true,
  created_at: '2026-03-01T10:00:00Z',
  updated_at: '2026-03-15T10:00:00Z',
};

const mockClientDetails = {
  101: {
    ...mockClients[0],
    proposals: [
      {
        id: 1,
        title: 'Propuesta Alpha',
        status: 'accepted',
        total_investment: 5000000,
        currency: 'COP',
        view_count: 5,
        sent_at: '2026-01-10T10:00:00Z',
      },
      {
        id: 2,
        title: 'Propuesta Beta',
        status: 'rejected',
        total_investment: 3000000,
        currency: 'COP',
        view_count: 2,
        sent_at: '2026-02-01T10:00:00Z',
      },
      {
        id: 3,
        title: 'Propuesta Gamma',
        status: 'sent',
        total_investment: 4000000,
        currency: 'USD',
        view_count: 0,
        sent_at: '2026-03-01T10:00:00Z',
      },
    ],
  },
  102: {
    ...mockClients[1],
    proposals: [
      {
        id: 4,
        title: 'Propuesta Delta',
        status: 'draft',
        total_investment: 2000000,
        currency: 'COP',
        view_count: 0,
        sent_at: null,
      },
    ],
  },
};

function setupMock(page, {
  clients = mockClients,
  details = mockClientDetails,
  onDelete = null,
  onCreate = null,
} = {}) {
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;

    if (apiPath === 'proposals/client-profiles/') {
      const requestUrl = new URL(route.request().url());
      const search = (requestUrl.searchParams.get('search') || '').toLowerCase().trim();
      const orphansParam = requestUrl.searchParams.get('orphans');
      let filtered = clients;
      if (orphansParam === 'true') filtered = clients.filter((c) => c.is_orphan);
      else if (orphansParam === 'false') filtered = clients.filter((c) => !c.is_orphan);
      if (search) {
        filtered = filtered.filter((c) => (
          c.name.toLowerCase().includes(search)
          || c.email.toLowerCase().includes(search)
          || (c.company || '').toLowerCase().includes(search)
        ));
      }
      return { status: 200, contentType: 'application/json', body: JSON.stringify(filtered) };
    }

    if (apiPath === 'proposals/client-profiles/create/' && method === 'POST') {
      if (onCreate) return onCreate(route);
      const body = JSON.parse(route.request().postData() || '{}');
      const newClient = {
        id: 201,
        name: body.name || 'Nuevo Cliente',
        email: body.email || 'cliente_201@temp.example.com',
        phone: body.phone || '',
        company: body.company || '',
        is_onboarded: false,
        is_email_placeholder: !body.email,
        total_proposals: 0,
        is_orphan: true,
      };
      return { status: 201, contentType: 'application/json', body: JSON.stringify(newClient) };
    }

    const deleteMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/delete\/$/);
    if (deleteMatch && method === 'DELETE') {
      if (onDelete) return onDelete(route, Number(deleteMatch[1]));
      return { status: 204, body: '' };
    }

    const detailMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/$/);
    if (detailMatch) {
      const clientId = Number(detailMatch[1]);
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(details[clientId] || { ...mockClients[0], proposals: [] }),
      };
    }
    return null;
  });
}

async function gotoClients(page) {
  await page.goto('/panel/clients');
  await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 30_000 });
}

test.describe('Admin Mini CRM Clients', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders client list with names, emails, and stats', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    await expect(page.getByText('Carlos López')).toBeVisible();
    await expect(page.getByText('Ana Martínez')).toBeVisible();
    await expect(page.getByText('carlos@test.com')).toBeVisible();
    await expect(page.getByText('ana@test.com')).toBeVisible();
    await expect(page.getByText('3 propuestas')).toBeVisible();
    await expect(page.getByText('1 propuesta', { exact: false })).toBeVisible();
  });

  test('expanding a client shows their proposals table', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    // Click on Carlos to expand
    await page.getByTestId('client-row-101').getByText('Carlos López').click();

    await expect(page.getByRole('link', { name: 'Propuesta Alpha' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Propuesta Beta' })).toBeVisible();
    await expect(page.getByText('accepted')).toBeVisible();
  });

  test('search filters clients by name or email', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    await page.getByTestId('clients-search-input').fill('ana');

    await expect(page.getByTestId('client-row-102')).toBeVisible();
    await expect(page.getByTestId('client-row-101')).not.toBeVisible();
  });

  test('empty state shows message when no clients exist', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, { clients: [] });
    await gotoClients(page);

    await expect(page.getByText('No hay clientes aún.')).toBeVisible();
  });
});

test.describe('Admin Clients — Tab filtering', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('Huérfanos tab shows only orphan clients', {
    tag: [...ADMIN_CLIENT_DELETE_ORPHAN, '@role:admin'],
  }, async ({ page }) => {
    const allClients = [...mockClients, mockOrphanClient];
    await setupMock(page, { clients: allClients });
    await gotoClients(page);

    // Switch to orphans tab
    await page.getByTestId('clients-tab-orphans').click();
    await expect(page.getByTestId(`client-row-${mockOrphanClient.id}`)).toBeVisible();
    await expect(page.getByTestId('client-row-101')).not.toBeVisible();
    await expect(page.getByTestId('client-row-102')).not.toBeVisible();
  });

  test('Activos tab hides orphan clients', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    const allClients = [...mockClients, mockOrphanClient];
    await setupMock(page, { clients: allClients });
    await gotoClients(page);

    await page.getByTestId('clients-tab-active').click();
    await expect(page.getByTestId('client-row-101')).toBeVisible();
    await expect(page.getByTestId('client-row-102')).toBeVisible();
    await expect(page.getByTestId(`client-row-${mockOrphanClient.id}`)).not.toBeVisible();
  });
});

test.describe('Admin Clients — Create standalone client', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('opens create modal, fills form, and new client appears in list', {
    tag: [...ADMIN_CLIENT_CREATE_STANDALONE, '@role:admin'],
  }, async ({ page }) => {
    // Use a mutable array so the list endpoint reflects the newly created client
    // after the page calls loadClients() post-creation.
    const dynamicClients = [...mockClients];
    await setupMock(page, {
      clients: dynamicClients,
      onCreate: async (route) => {
        const body = JSON.parse(route.request().postData() || '{}');
        const newClient = {
          id: 201, name: body.name || 'Nuevo Cliente Test',
          email: body.email || 'cliente_201@temp.example.com',
          phone: body.phone || '', company: body.company || '',
          is_onboarded: false, is_email_placeholder: !body.email,
          total_proposals: 0, is_orphan: true,
        };
        dynamicClients.unshift(newClient);
        return { status: 201, contentType: 'application/json', body: JSON.stringify(newClient) };
      },
    });
    await gotoClients(page);

    // Open modal
    await page.getByTestId('clients-new-button').click();
    await expect(page.getByTestId('clients-new-name')).toBeVisible();

    // Fill form
    await page.getByTestId('clients-new-name').fill('Nuevo Cliente Test');
    await page.getByTestId('clients-new-email').fill('nuevo@test.com');
    await page.getByTestId('clients-new-company').fill('Test Corp');

    // Submit and wait for modal to close (success)
    await page.getByTestId('clients-new-submit').click();
    await expect(page.getByTestId('clients-new-submit')).not.toBeVisible({ timeout: 5_000 });

    // New client should appear in the list (reloaded after creation)
    await expect(page.getByTestId('client-row-201')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Nuevo Cliente Test')).toBeVisible();
  });

  test('create client without email generates placeholder badge', {
    tag: [...ADMIN_CLIENT_CREATE_STANDALONE, '@role:admin'],
  }, async ({ page }) => {
    const dynamicClients = [...mockClients];
    await setupMock(page, {
      clients: dynamicClients,
      onCreate: async (route) => {
        const body = JSON.parse(route.request().postData() || '{}');
        const newClient = {
          id: 201, name: body.name || 'Sin Email Test',
          email: 'cliente_201@temp.example.com',
          phone: '', company: '',
          is_onboarded: false, is_email_placeholder: true,
          total_proposals: 0, is_orphan: true,
        };
        dynamicClients.unshift(newClient);
        return { status: 201, contentType: 'application/json', body: JSON.stringify(newClient) };
      },
    });
    await gotoClients(page);

    await page.getByTestId('clients-new-button').click();
    await page.getByTestId('clients-new-name').fill('Sin Email Test');
    // Leave email blank intentionally

    await page.getByTestId('clients-new-submit').click();
    await expect(page.getByTestId('clients-new-submit')).not.toBeVisible({ timeout: 5_000 });

    // Client row appears with placeholder badge
    await expect(page.getByTestId('client-row-201')).toBeVisible({ timeout: 10_000 });
    // The placeholder badge text
    await expect(page.getByTestId('client-row-201').getByText(/placeholder/i)).toBeVisible();
  });
});

test.describe('Admin Clients — Delete orphan client', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('trash icon is visible only on orphan rows', {
    tag: [...ADMIN_CLIENT_DELETE_ORPHAN, '@role:admin'],
  }, async ({ page }) => {
    const allClients = [...mockClients, mockOrphanClient];
    await setupMock(page, { clients: allClients });
    await gotoClients(page);

    // Orphan has trash button
    await expect(page.getByTestId(`client-delete-${mockOrphanClient.id}`)).toBeVisible();
    // Active clients do NOT have trash button
    await expect(page.getByTestId('client-delete-101')).not.toBeVisible();
    await expect(page.getByTestId('client-delete-102')).not.toBeVisible();
  });

  test('deleting orphan removes it from the list after confirmation', {
    tag: [...ADMIN_CLIENT_DELETE_ORPHAN, '@role:admin'],
  }, async ({ page }) => {
    const allClients = [...mockClients, mockOrphanClient];
    await setupMock(page, { clients: allClients });
    await gotoClients(page);

    // Click trash
    await page.getByTestId(`client-delete-${mockOrphanClient.id}`).click();

    // Confirm modal should appear — use exact "Eliminar" to avoid matching the trash icon title
    const confirmBtn = page.getByRole('button', { name: 'Eliminar', exact: true });
    await expect(confirmBtn).toBeVisible({ timeout: 5_000 });
    await confirmBtn.click();

    // Client row should be gone
    await expect(page.getByTestId(`client-row-${mockOrphanClient.id}`)).not.toBeVisible({ timeout: 5_000 });
  });

  test('active client does not show trash icon (protected from accidental delete)', {
    tag: [...ADMIN_CLIENT_DELETE_PROTECTED, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoClients(page);

    // No trash icon for clients that have proposals
    await expect(page.getByTestId('client-delete-101')).not.toBeVisible();
    await expect(page.getByTestId('client-delete-102')).not.toBeVisible();
  });
});
