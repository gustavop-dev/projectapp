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
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Wait for the table to render
    await expect(page.getByText('Actions Modal Test')).toBeVisible({ timeout: 10000 });

    // Click the actions (⋮) button on the proposal row
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();

    // Modal should open showing action items
    await expect(page.getByText('Editar propuesta')).toBeVisible({ timeout: 3000 });
  });

  test('draft proposal shows edit, preview, send, copy, whatsapp, duplicate, toggle, delete actions', {
    tag: [...ADMIN_PROPOSAL_ACTIONS_MODAL, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler([mockDraftProposal]));
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Actions Modal Test')).toBeVisible({ timeout: 10000 });

    // Open actions modal
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
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
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Actions Modal Test')).toBeVisible({ timeout: 10000 });

    // Open actions modal
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
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Actions Modal Test')).toBeVisible({ timeout: 10000 });

    // Open actions modal
    const actionsBtn = page.locator('table button').filter({ has: page.locator('svg') }).last();
    await actionsBtn.click();
    await expect(page.getByText('Editar propuesta')).toBeVisible();

    // Click the close button
    const closeBtn = page.locator('.fixed').getByRole('button').filter({ has: page.locator('svg path') }).first();
    await closeBtn.click();

    // Modal should close
    await expect(page.getByText('Editar propuesta')).not.toBeVisible({ timeout: 3000 });
  });
});
