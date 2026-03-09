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
    client_name: 'Carlos López',
    client_email: 'carlos@test.com',
    total_proposals: 3,
    accepted: 1,
    rejected: 1,
    pending: 1,
    last_status: 'sent',
    proposals: [
      { id: 1, title: 'Propuesta Alpha', status: 'accepted', total_investment: 5000000, currency: 'COP', view_count: 5, sent_at: '2026-01-10T10:00:00Z', rejection_reason: null, rejection_comment: null },
      { id: 2, title: 'Propuesta Beta', status: 'rejected', total_investment: 3000000, currency: 'COP', view_count: 2, sent_at: '2026-02-01T10:00:00Z', rejection_reason: 'Precio alto', rejection_comment: 'Excede presupuesto' },
      { id: 3, title: 'Propuesta Gamma', status: 'sent', total_investment: 4000000, currency: 'USD', view_count: 0, sent_at: '2026-03-01T10:00:00Z', rejection_reason: null, rejection_comment: null },
    ],
  },
  {
    client_name: 'Ana Martínez',
    client_email: 'ana@test.com',
    total_proposals: 1,
    accepted: 0,
    rejected: 0,
    pending: 1,
    last_status: 'draft',
    proposals: [
      { id: 4, title: 'Propuesta Delta', status: 'draft', total_investment: 2000000, currency: 'COP', view_count: 0, sent_at: null, rejection_reason: null, rejection_comment: null },
    ],
  },
];

function setupMock(page, { clients = mockClients } = {}) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/clients/') return { status: 200, contentType: 'application/json', body: JSON.stringify(clients) };
    return null;
  });
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
    await page.goto('/panel/clients');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible();
    await expect(page.getByText('Carlos López')).toBeVisible();
    await expect(page.getByText('Ana Martínez')).toBeVisible();
    await expect(page.getByText('3 propuestas')).toBeVisible();
    await expect(page.getByText('1 propuesta', { exact: false })).toBeVisible();
  });

  test('expanding a client shows their proposals table', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/clients');
    await page.waitForLoadState('networkidle');

    // Click on Carlos to expand
    await page.getByText('Carlos López').click();

    await expect(page.getByRole('link', { name: 'Propuesta Alpha' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Propuesta Beta' })).toBeVisible();
    await expect(page.getByText('Precio alto')).toBeVisible();
  });

  test('search filters clients by name or email', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/clients');
    await page.waitForLoadState('networkidle');

    await page.getByPlaceholder('Buscar por nombre o email...').fill('ana');

    await expect(page.getByText('Ana Martínez')).toBeVisible();
    await expect(page.getByText('Carlos López')).not.toBeVisible();
  });

  test('empty state shows message when no clients exist', {
    tag: [...ADMIN_MINI_CRM_CLIENTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, { clients: [] });
    await page.goto('/panel/clients');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('No hay clientes aún.')).toBeVisible();
  });
});
