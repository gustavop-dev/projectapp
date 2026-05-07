/**
 * E2E tests for the proposal-to-platform handoff action.
 *
 * @flow:admin-proposal-platform-handoff
 *
 * Covers: after a proposal is accepted, the admin opens the actions modal
 * from the edit page and clicks "Lanzar a Plataforma". The frontend POSTs
 * to /api/proposals/<id>/launch-to-platform/ and the success path renders
 * a confirmation toast when platform_onboarding_status === 'completed'.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_PLATFORM_HANDOFF } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 42;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function makeAcceptedProposal(overrides = {}) {
  return {
    id: PROPOSAL_ID,
    uuid: 'aaaa1111-bbbb-2222-cccc-3333dddd4444',
    slug: 'cliente-aceptado',
    title: 'Propuesta Aceptada — Lanzamiento',
    client_name: 'Cliente Aceptado',
    client_email: 'cliente@example.com',
    status: 'accepted',
    language: 'es',
    total_investment: '15000000',
    currency: 'COP',
    view_count: 5,
    sent_at: '2026-04-01T10:00:00Z',
    accepted_at: '2026-04-15T10:00:00Z',
    expires_at: new Date(Date.now() + 30 * 86400000).toISOString(),
    is_active: true,
    sections: [],
    requirement_groups: [],
    change_logs: [],
    proposal_documents: [],
    public_url: '/proposal/cliente-aceptado',
    platform_onboarding_completed_at: null,
    platform_onboarding_status: null,
    ...overrides,
  };
}

test.describe('Admin Proposal — Platform Handoff (launch-to-platform)', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('accepted proposal exposes "Lanzar a Plataforma" in the actions modal', {
    tag: [...ADMIN_PROPOSAL_PLATFORM_HANDOFF, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(makeAcceptedProposal()) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    const actionsBtn = page.getByTestId('proposal-actions-menu');
    await expect(actionsBtn).toBeVisible({ timeout: 15000 });
    await actionsBtn.click();

    await expect(page.getByTestId('proposal-action-launch')).toBeVisible({ timeout: 5000 });
  });

  test('clicking "Lanzar a Plataforma" POSTs to launch-to-platform/ with force=false', {
    tag: [...ADMIN_PROPOSAL_PLATFORM_HANDOFF, '@role:admin'],
  }, async ({ page }) => {
    let capturedForce = null;
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(makeAcceptedProposal()) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/launch-to-platform/` && method === 'POST') {
        const raw = route.request().postData();
        if (raw) capturedForce = JSON.parse(raw).force;
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(
            makeAcceptedProposal({
              platform_onboarding_status: 'completed',
              platform_onboarding_completed_at: new Date().toISOString(),
            }),
          ),
        };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    const actionsBtn = page.getByTestId('proposal-actions-menu');
    await expect(actionsBtn).toBeVisible({ timeout: 15000 });
    await actionsBtn.click();

    const launchAction = page.getByTestId('proposal-action-launch');
    await expect(launchAction).toBeVisible({ timeout: 5000 });
    await launchAction.click();

    await expect(() => expect(capturedForce).toBe(false)).toPass({ timeout: 10000 });
  });

  test('successful handoff shows confirmation toast', {
    tag: [...ADMIN_PROPOSAL_PLATFORM_HANDOFF, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(makeAcceptedProposal()) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/launch-to-platform/` && method === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(
            makeAcceptedProposal({
              platform_onboarding_status: 'completed',
              platform_onboarding_completed_at: new Date().toISOString(),
            }),
          ),
        };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`, { waitUntil: 'domcontentloaded' });

    await page.getByTestId('proposal-actions-menu').click();
    await page.getByTestId('proposal-action-launch').click();

    await expect(page.getByText(/Propuesta lanzada a la plataforma\./)).toBeVisible({ timeout: 10000 });
  });
});
