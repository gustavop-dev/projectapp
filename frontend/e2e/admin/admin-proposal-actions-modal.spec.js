/**
 * E2E tests for the admin proposal actions modal.
 *
 * Covers: opening the modal from listing, verifying action items render
 * with icons and info tooltips, conditional send/resend visibility.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_ACTIONS_MODAL } from '../helpers/flow-tags.js';

const mockDraftProposal = {
  id: 1,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Actions Modal Test',
  client_name: 'Test Client',
  client_email: 'client@test.com',
  client_phone: '+573001234567',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  heat_score: 5,
  sent_at: null,
  is_active: true,
  created_at: '2026-03-01T12:00:00Z',
};

const mockSentProposal = {
  ...mockDraftProposal,
  id: 2,
  uuid: '22222222-2222-2222-2222-222222222222',
  status: 'sent',
  sent_at: '2026-03-02T12:00:00Z',
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
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: 2, conversion_rate: 50 }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  };
}

test.describe('Admin Proposal Actions Modal', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8300, role: 'admin', is_staff: true },
    });
  });

  test('clicking actions button opens modal with proposal title', {
    tag: [...ADMIN_PROPOSAL_ACTIONS_MODAL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockDraftProposal]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Test Client')).toBeVisible({ timeout: 15000 });

    // quality: allow-fragile-selector (table actions button has no testid, last SVG button in row is the actions trigger)
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();

    // Modal should open showing action items
    await expect(page.getByText('Editar propuesta')).toBeVisible({ timeout: 3000 });
  });

  test('draft proposal shows edit, preview, send, copy, whatsapp, duplicate, toggle, delete actions', {
    tag: [...ADMIN_PROPOSAL_ACTIONS_MODAL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockDraftProposal]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await page.getByText('Test Client').waitFor({ state: 'visible', timeout: 15000 });

    // quality: allow-fragile-selector (table actions button has no testid)
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.waitFor({ state: 'visible', timeout: 5000 });
    await actionsBtn.click();

    // Verify core actions are present
    await expect(page.getByText('Editar propuesta')).toBeVisible();
    await expect(page.getByText('Ver preview')).toBeVisible();
    await expect(page.getByText('Enviar al cliente')).toBeVisible();
    await expect(page.getByText('Copiar enlace')).toBeVisible();
    await expect(page.getByText('Enviar por WhatsApp')).toBeVisible();
    await expect(page.getByText('Duplicar propuesta')).toBeVisible();
    await expect(page.getByText('Eliminar')).toBeVisible();
  });

  test('sent proposal shows resend instead of send', {
    tag: [...ADMIN_PROPOSAL_ACTIONS_MODAL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockSentProposal]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Test Client')).toBeVisible({ timeout: 15000 });

    // quality: allow-fragile-selector (table actions button has no testid)
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();

    // Should show re-send, not send
    await expect(page.getByText('Re-enviar email')).toBeVisible();
    await expect(page.getByText('Enviar al cliente')).not.toBeVisible();
  });

  test('closing modal by clicking backdrop', {
    tag: [...ADMIN_PROPOSAL_ACTIONS_MODAL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockDraftProposal]));
    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Test Client')).toBeVisible({ timeout: 15000 });

    // quality: allow-fragile-selector (table actions button has no testid)
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();
    await expect(page.getByText('Editar propuesta')).toBeVisible({ timeout: 5000 });

    // Overlay uses @click.self on fixed inset-0; avoid page.locator('.fixed').first() (sidebar wins).
    const modalOverlay = page.locator('div.fixed.inset-0').filter({
      has: page.getByRole('heading', { level: 3, name: mockDraftProposal.title }),
    });
    await modalOverlay.click({ position: { x: 8, y: 8 } });

    await expect(page.getByText('Editar propuesta')).not.toBeVisible({ timeout: 5000 });
  });
});

/**
 * The edit page (/panel/proposals/:id/edit) mounts a different actions modal
 * (BusinessProposal/admin/ProposalActionsModal.vue) whose "Lanzar a Plataforma"
 * action was widened to show for `negotiating` proposals, not only `accepted`.
 */
const futureDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const mockEditProposal = (overrides = {}) => ({
  id: 3,
  uuid: '33333333-3333-3333-3333-333333333333',
  title: 'Launch Action Proposal',
  client_name: 'Nego Client',
  client_email: 'nego@test.com',
  status: 'negotiating',
  language: 'es',
  total_investment: '8000000',
  currency: 'COP',
  discount_percent: 0,
  available_transitions: ['accepted', 'rejected'],
  platform_onboarding_completed_at: null,
  view_count: 4,
  sent_at: '2026-03-02T12:00:00Z',
  expires_at: futureDate,
  is_active: true,
  sections: [
    { id: 30, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true, content_json: { clientName: 'Nego Client' } },
  ],
  requirement_groups: [],
  ...overrides,
});

function setupEditMocks(page, proposal) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true } });
    if (apiPath === `proposals/${proposal.id}/detail/`) return json(proposal);
    return null;
  });
}

test.describe('Proposal Actions Modal — edit page launch action', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8300, role: 'admin', is_staff: true },
    });
  });

  test('launch-to-platform action is available while the proposal is negotiating', {
    tag: [...ADMIN_PROPOSAL_ACTIONS_MODAL, '@role:admin'],
  }, async ({ page }) => {
    const proposal = mockEditProposal({ status: 'negotiating' });
    await setupEditMocks(page, proposal);

    await page.goto(`/panel/proposals/${proposal.id}/edit`, { waitUntil: 'domcontentloaded' });

    await page.getByTestId('proposal-actions-menu').click();

    const launch = page.getByTestId('proposal-action-launch');
    await expect(launch).toBeVisible({ timeout: 15000 });
    await expect(launch).toContainText('Lanzar a Plataforma');
  });
});
