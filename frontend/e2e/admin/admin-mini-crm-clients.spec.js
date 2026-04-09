/**
 * E2E tests for admin mini CRM clients page.
 *
 * Covers: client list rendering, search filtering, expanding client
 * to see proposals, and empty state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_MINI_CRM_CLIENTS } from '../helpers/flow-tags.js';

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

function setupMock(page, { clients = mockClients, details = mockClientDetails } = {}) {
  return mockApi(page, async ({ route, apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/client-profiles/') {
      const requestUrl = new URL(route.request().url());
      const search = (requestUrl.searchParams.get('search') || '').toLowerCase().trim();
      const filtered = search
        ? clients.filter((client) => (
          client.name.toLowerCase().includes(search)
          || client.email.toLowerCase().includes(search)
          || client.company.toLowerCase().includes(search)
        ))
        : clients;
      return { status: 200, contentType: 'application/json', body: JSON.stringify(filtered) };
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
  await page.waitForLoadState('domcontentloaded');
  await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible();
}

test.describe('Admin Mini CRM Clients', () => {
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
