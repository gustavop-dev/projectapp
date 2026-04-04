/**
 * E2E tests for admin proposal edit flow.
 *
 * Covers: page heading, tab rendering, General tab form fields.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_EDIT } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Propuesta E2E',
  client_name: 'Cliente Edit E2E',
  client_email: 'edit@e2e.com',
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
  sections: [],
  requirement_groups: [],
};

function buildMockHandler() {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    if (apiPath === 'proposals/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProposal]) };
    }
    return null;
  };
}

test.describe('Admin Proposal Edit', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8200, role: 'admin', is_staff: true } });
  });

  test('renders proposal title in page heading', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
  });

  test('renders General and Secciones navigation tabs', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole('button', { name: 'General' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Secciones' })).toBeVisible();
  });

  test('shows client name field pre-filled in General tab', {
    tag: [...ADMIN_PROPOSAL_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Propuesta E2E')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('input[type="text"][required]').nth(1)).toHaveValue('Cliente Edit E2E');
  });
});
