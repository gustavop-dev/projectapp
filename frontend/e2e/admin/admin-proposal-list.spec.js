/**
 * E2E tests for admin proposal list view.
 *
 * Covers: client-side search filtering of the table, and the empty state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_LIST } from '../helpers/flow-tags.js';

const proposalA = {
  id: 1, uuid: '11111111-1111-1111-1111-111111111111', title: 'Plataforma E2E',
  client_name: 'Cliente E2E', client_email: 'a@e2e.com', client_phone: '+573001234567',
  status: 'draft', language: 'es', total_investment: '5000000', currency: 'COP',
  view_count: 0, heat_score: 5, sent_at: null, is_active: true, created_at: '2026-01-01T12:00:00Z',
};
const proposalB = {
  ...proposalA, id: 2, uuid: '22222222-2222-2222-2222-222222222222', title: 'Sitio Corporativo',
  client_name: 'ACME Corp', client_email: 'b@acme.com', client_phone: '+573009999999',
};

function buildMockHandler(proposals) {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === 'proposals/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposals) };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: proposals.length, conversion_rate: 0 }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  };
}

test.describe('Admin Proposal List', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('filtering by client name narrows the table to the matching proposal', {
    tag: [...ADMIN_PROPOSAL_LIST, '@role:admin'],
  }, async ({ page }) => {
    // Fails if the search box stops filtering the proposal table by title/client.
    await mockApi(page, buildMockHandler([proposalA, proposalB]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Cliente E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText('ACME Corp')).toBeVisible();

    await page.getByPlaceholder('Buscar por título o cliente...').fill('ACME');

    // Only the matching row survives; the non-matching one is filtered out.
    await expect(page.getByText('ACME Corp')).toBeVisible();
    await expect(page.getByText('Cliente E2E')).not.toBeVisible();
  });

  test('shows the empty state when the proposal list is empty', {
    tag: [...ADMIN_PROPOSAL_LIST, '@role:admin'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (empty-state render assertion; the list's
    // interaction is covered by the filter test above)
    await mockApi(page, buildMockHandler([]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('table')).toHaveCount(0);
  });
});
