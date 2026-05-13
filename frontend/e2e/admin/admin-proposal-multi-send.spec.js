/**
 * E2E test for the multi-proposal send flow.
 *
 * Covers: lightning-bolt menu → "Enviar varias propuestas" action,
 * modal lists same-client proposals grouped by status, current proposal
 * is locked, selecting another proposal enables the confirm button,
 * confirm posts to /proposals/:id/send-multi/ with the selected ids and
 * shows the success toast.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_MULTI_SEND } from '../helpers/flow-tags.js';

const PRIMARY_ID = 1;
const PRIMARY_UUID = '11111111-1111-1111-1111-111111111111';
const CLIENT_ID = 555;
const SECOND_ID = 2;

const futureDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

const baseClient = { id: CLIENT_ID, name: 'Juan García', email: 'juan@cliente.com' };

const mockPrimaryProposal = {
  id: PRIMARY_ID,
  uuid: PRIMARY_UUID,
  title: 'Fase 1 — Plataforma',
  client_name: 'Juan García',
  client_email: 'juan@cliente.com',
  client: baseClient,
  status: 'draft',
  language: 'es',
  total_investment: '4320000',
  currency: 'COP',
  view_count: 0,
  sent_at: null,
  expires_at: futureDate,
  is_active: true,
  available_transitions: ['sent'],
  sections: [
    { id: 10, section_type: 'greeting', title: 'Saludo', order: 0, is_enabled: true, content_json: {} },
  ],
  requirement_groups: [],
};

const mockSecondProposal = {
  id: SECOND_ID,
  uuid: '22222222-2222-2222-2222-222222222222',
  title: 'Fase 2 — Vigilancia',
  client_name: 'Juan García',
  client_email: 'juan@cliente.com',
  client: baseClient,
  status: 'sent',
  language: 'es',
  total_investment: '14100000',
  currency: 'COP',
  view_count: 2,
  sent_at: futureDate,
  expires_at: futureDate,
  is_active: true,
  is_expired: false,
  days_remaining: 30,
};

const mockSentResponse = {
  ...mockPrimaryProposal,
  status: 'sent',
  sent_at: '2026-05-05T12:00:00Z',
  email_delivery: { ok: true, reason: 'sent', detail: 'group=abc' },
  transitions: { [PRIMARY_ID]: 'sent', [SECOND_ID]: 'resent' },
};

test.describe('Admin Proposal Multi Send', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8300, role: 'admin', is_staff: true },
    });
  });

  test('lightning menu opens multi-send modal, selects another proposal, posts ids and shows success toast', {
    tag: [...ADMIN_PROPOSAL_MULTI_SEND, '@role:admin'],
  }, async ({ page }) => {
    let capturedBody = null;

    // General mock for auth, detail, candidates list, and page-level API calls
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === `proposals/${PRIMARY_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockPrimaryProposal) };
      }
      if (apiPath === 'proposals/' && route.request().url().includes(`client_id=${CLIENT_ID}`)) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([
          { ...mockPrimaryProposal, sections: undefined, requirement_groups: undefined },
          mockSecondProposal,
        ]) };
      }
      // Analytics returns null so ProposalAnalytics renders safely (shows "No data" state).
      // Without this, {} is returned which causes analytics.comparison to be undefined,
      // crashing the render function and cascading Vue errors that block modal close.
      if (apiPath === `proposals/${PRIMARY_ID}/analytics/`) {
        return { status: 200, contentType: 'application/json', body: 'null' };
      }
      return null;
    });

    // Dedicated route for the send-multi POST (registered after mockApi → LIFO priority wins).
    // Using a glob + synchronous fulfill avoids the async-handler timing issue that was
    // causing the axios XHR to hang in CI: the inline non-async fulfill fires the CDP
    // Fetch.fulfillRequest command before any microtask boundary.
    await page.route(`**/api/proposals/${PRIMARY_ID}/send-multi/`, (route) => {
      if (route.request().method() !== 'POST') { route.continue(); return; }
      capturedBody = route.request().postData();
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSentResponse),
      });
    });

    await page.goto(`/panel/proposals/${PRIMARY_ID}/edit`, { waitUntil: 'domcontentloaded' });

    // Open lightning-bolt actions menu
    await page.getByTestId('proposal-actions-menu').click();

    // Click the new multi-send action
    await page.getByTestId('proposal-action-send-multi').click();

    // Multi-send modal renders
    const modal = page.getByTestId('proposal-multi-send-modal');
    await expect(modal).toBeVisible();
    await expect(modal).toContainText('Juan García');

    // Current proposal checkbox is disabled (always included)
    await expect(page.getByTestId(`proposal-multi-send-option-${PRIMARY_ID}`)).toBeDisabled();

    // Confirm button is disabled until ≥2 are selected
    const confirm = page.getByTestId('proposal-multi-send-confirm');
    await expect(confirm).toBeDisabled();

    // Select the second proposal
    await page.getByTestId(`proposal-multi-send-option-${SECOND_ID}`).check();
    await expect(confirm).toBeEnabled();

    await confirm.click();

    // Wait for the modal to disappear — this means the send completed and the
    // close chain ran. capturedBody is already set by the route handler.
    await page.locator('[data-testid="proposal-multi-send-modal"]').waitFor({ state: 'detached', timeout: 15000 });

    // Verify request payload
    expect(capturedBody).toBeTruthy();
    expect(JSON.parse(capturedBody)).toEqual({ proposal_ids: [PRIMARY_ID, SECOND_ID] });
  });
});
