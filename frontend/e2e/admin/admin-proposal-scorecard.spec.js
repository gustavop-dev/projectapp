/**
 * E2E tests for the pre-send scorecard.
 *
 * Covers: the scorecard modal fetches proposals/:id/scorecard/ and renders
 * the score badge + check list, a passing scorecard enables the confirm
 * button, and blockers (can_send: false) disable it with the "bloqueante"
 * tag visible.
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
    { key: 'estimated_weeks', label: 'Tiempo estimado definido', passed: false, blocker: false },
  ],
};

const mockScorecardFail = {
  score: 3,
  can_send: false,
  total_checks: 10,
  passed_checks: 3,
  blockers: [
    { key: 'total_investment', label: 'Inversión total > $0', passed: false, blocker: true },
  ],
  checks: [
    { key: 'client_email', label: 'Email del cliente', passed: true, blocker: true },
    { key: 'client_name', label: 'Nombre del cliente', passed: true, blocker: true },
    { key: 'total_investment', label: 'Inversión total > $0', passed: false, blocker: true },
    { key: 'expires_at', label: 'Fecha de expiración futura', passed: false, blocker: true },
    { key: 'enabled_sections', label: 'Al menos 1 sección habilitada', passed: false, blocker: true },
  ],
};

function buildHandler({ scorecard }) {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === 'proposals/1/detail/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    if (apiPath === 'proposals/1/scorecard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(scorecard) };
    }
    return null;
  };
}

test.describe('Admin Proposal Scorecard', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('passing scorecard renders score badge, checks, and enables the confirm button', {
    tag: [...ADMIN_PROPOSAL_SCORECARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ scorecard: mockScorecardPass }));

    await page.goto('/panel/proposals/1/edit', { waitUntil: 'domcontentloaded' });

    await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/1/scorecard/')),
      page.getByRole('button', { name: 'Enviar al Cliente' }).first().click(),
    ]);

    const modal = page.getByLabel('Scorecard pre-envío');
    await expect(modal).toBeVisible();
    await expect(modal.getByText('9/10')).toBeVisible();
    await expect(modal.getByText('Email del cliente')).toBeVisible();
    // Failed non-blocker shows without the "bloqueante" tag.
    await expect(modal.getByText('Tiempo estimado definido')).toBeVisible();
    await expect(modal.getByText('bloqueante')).not.toBeVisible();
    // A passing scorecard (can_send: true) keeps the confirm button enabled.
    await expect(modal.getByRole('button', { name: 'Enviar al Cliente' })).toBeEnabled();
  });

  test('scorecard with blockers disables sending and tags the blockers', {
    tag: [...ADMIN_PROPOSAL_SCORECARD, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ scorecard: mockScorecardFail }));

    await page.goto('/panel/proposals/1/edit', { waitUntil: 'domcontentloaded' });

    await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/1/scorecard/')),
      page.getByRole('button', { name: 'Enviar al Cliente' }).first().click(),
    ]);

    const modal = page.getByLabel('Scorecard pre-envío');
    await expect(modal).toBeVisible();
    await expect(modal.getByText('3/10')).toBeVisible();
    await expect(modal.getByText('Inversión total > $0')).toBeVisible();
    await expect(modal.getByText('bloqueante').first()).toBeVisible();
    // can_send: false must disable the modal's confirm button.
    await expect(modal.getByRole('button', { name: 'Enviar al Cliente' })).toBeDisabled();
  });
});
