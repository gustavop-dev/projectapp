/**
 * E2E tests for admin proposal list view.
 *
 * Covers: page heading, proposal table rendering, empty state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_LIST } from '../helpers/flow-tags.js';

const mockProposal = {
  id: 1,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Plataforma E2E',
  client_name: 'Cliente E2E',
  client_email: 'cliente@e2e.com',
  client_phone: '+573001234567',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  heat_score: 5,
  sent_at: null,
  is_active: true,
  created_at: '2026-01-01T12:00:00Z',
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

  test('renders Propuestas heading with new proposal button', {
    tag: [...ADMIN_PROPOSAL_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockProposal]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole('link', { name: /nueva propuesta/i })).toBeVisible();
  });

  test('shows client name and phone in table row', {
    tag: [...ADMIN_PROPOSAL_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockProposal]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Cliente E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText('+573001234567')).toBeVisible();
  });

  test('shows empty state when proposals list is empty', {
    tag: [...ADMIN_PROPOSAL_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Propuestas' })).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('table')).not.toBeAttached();
  });
});
