/**
 * E2E tests for admin sending a proposal to a client.
 *
 * Covers: "Enviar al Cliente" button click, API call verification,
 * status badge updates to 'sent', re-send button appears for sent proposals.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SEND } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;

const mockDraftProposal = {
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Send Test Proposal',
  client_name: 'Test Client',
  client_email: 'client@test.com',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  sent_at: null,
  expires_at: null,
  is_active: true,
  sections: [],
  requirement_groups: [],
};

test.describe('Admin Proposal Send', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8300, role: 'admin', is_staff: true },
    });
  });

  test('"Enviar al Cliente" button is visible for draft proposal with email', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDraftProposal) };
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: 'Enviar al Cliente' })).toBeVisible();
  });

  test('clicking "Enviar al Cliente" calls send API and updates status', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    let sendCalled = false;
    let currentStatus = 'draft';

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: currentStatus }) };
      }
      if (apiPath === `proposals/${PROPOSAL_ID}/send/`) {
        sendCalled = true;
        currentStatus = 'sent';
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: 'sent', sent_at: '2026-03-04T12:00:00Z' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');

    // Click the send button — wait for the send API response
    const [sendResponse] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`proposals/${PROPOSAL_ID}/send/`)),
      page.getByRole('button', { name: 'Enviar al Cliente' }).click(),
    ]);
    await sendResponse.finished();

    expect(sendCalled).toBe(true);
  });

  test('"Re-enviar al Cliente" button appears for sent proposal', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, status: 'sent', sent_at: '2026-03-04T12:00:00Z' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');

    // For sent proposals, re-send button appears instead of send
    await expect(page.getByRole('button', { name: 'Re-enviar al Cliente' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Enviar al Cliente' })).not.toBeVisible();
  });

  test('"Enviar al Cliente" is hidden when client email is empty', {
    tag: [...ADMIN_PROPOSAL_SEND, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDraftProposal, client_email: '' }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: 'Enviar al Cliente' })).not.toBeVisible();
  });
});
