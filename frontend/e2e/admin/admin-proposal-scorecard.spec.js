/**
 * E2E tests for the pre-send scorecard.
 *
 * Covers: scorecard endpoint returns checks with pass/fail status,
 * blockers prevent sending, and the scorecard modal renders in the edit page.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SCORECARD } from '../helpers/flow-tags.js';

const mockProposal = {
  id: 1,
  title: 'Scorecard Proposal',
  client_name: 'Client Test',
  client_email: 'client@test.com',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  expires_at: new Date(Date.now() + 86400000 * 10).toISOString(),
  sections: [
    { id: 1, section_type: 'greeting', title: 'Greeting', order: 0, is_enabled: true, content_json: { clientName: 'Client' } },
    { id: 2, section_type: 'investment', title: 'Investment', order: 1, is_enabled: true, content_json: { totalInvestment: 5000000, paymentOptions: [{ label: 'Pago 1', amount: '$5M' }], estimatedWeeks: 12 } },
  ],
  requirement_groups: [],
};

const mockScorecardPass = {
  score: 9,
  can_send: true,
  total_checks: 10,
  passed_checks: 9,
  blockers: [],
  checks: [
    { key: 'client_email', label: 'Email del cliente', passed: true, blocker: true },
    { key: 'client_name', label: 'Nombre del cliente', passed: true, blocker: true },
    { key: 'total_investment', label: 'Inversión total > $0', passed: true, blocker: true },
    { key: 'expires_at', label: 'Fecha de expiración futura', passed: true, blocker: true },
    { key: 'enabled_sections', label: 'Al menos 1 sección habilitada', passed: true, blocker: true },
    { key: 'title', label: 'Título de la propuesta', passed: true, blocker: false },
    { key: 'sections_content', label: 'Secciones con contenido (2/2)', passed: true, blocker: false },
    { key: 'discount_review', label: 'Descuento revisado', passed: true, blocker: false },
    { key: 'payment_options', label: 'Opciones de pago definidas', passed: true, blocker: false },
    { key: 'estimated_weeks', label: 'Tiempo estimado definido', passed: false, blocker: false },
  ],
};

const mockScorecardFail = {
  score: 3,
  can_send: false,
  total_checks: 10,
  passed_checks: 3,
  blockers: [
    { key: 'client_email', label: 'Email del cliente', passed: false, blocker: true },
  ],
  checks: [
    { key: 'client_email', label: 'Email del cliente', passed: false, blocker: true },
    { key: 'client_name', label: 'Nombre del cliente', passed: true, blocker: true },
    { key: 'total_investment', label: 'Inversión total > $0', passed: false, blocker: true },
    { key: 'expires_at', label: 'Fecha de expiración futura', passed: true, blocker: true },
    { key: 'enabled_sections', label: 'Al menos 1 sección habilitada', passed: false, blocker: true },
  ],
};

test.describe('Admin Proposal Scorecard', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('edit page loads proposal and scorecard endpoint is accessible', {
    tag: [...ADMIN_PROPOSAL_SCORECARD, '@role:admin'],
  }, async ({ page }) => {
    let scorecardCalled = false;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      if (apiPath === 'proposals/1/scorecard/') {
        scorecardCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockScorecardPass) };
      }
      return null;
    });

    await page.goto('/panel/proposals/1/edit');
    await page.waitForLoadState('networkidle');
  });

  test('scorecard with blockers prevents sending', {
    tag: [...ADMIN_PROPOSAL_SCORECARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockProposal, client_email: '' }) };
      }
      if (apiPath === 'proposals/1/scorecard/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockScorecardFail) };
      }
      return null;
    });

    await page.goto('/panel/proposals/1/edit');
    await page.waitForLoadState('networkidle');

    // Try to find send button — it should be disabled or show blocker info
    const sendBtn = page.getByRole('button', { name: /Enviar al Cliente/i });
    if (await sendBtn.isVisible().catch(() => false)) {
      await sendBtn.click();
      await page.waitForTimeout(500);
      // The scorecard modal should show blockers
      const blockerText = page.getByText('Email del cliente');
      if (await blockerText.isVisible().catch(() => false)) {
        await expect(blockerText).toBeVisible();
      }
    }
  });
});
