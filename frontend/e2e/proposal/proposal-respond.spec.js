/**
 * E2E tests for client responding to a proposal (accept/reject).
 *
 * Covers: navigating to the closing panel, clicking accept/reject buttons,
 * confirming in the modal, verifying API call and success state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_RESPOND } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockSentProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Test Proposal',
  client_name: 'Test Client',
  status: 'sent',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  sections: [
    {
      id: 1,
      section_type: 'greeting',
      title: '👋 Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Test Client', inspirationalQuote: '' },
    },
  ],
  requirement_groups: [],
};

/**
 * Helper: navigate to the last panel (proposal_closing) which contains
 * the accept/reject buttons. Waits for the preloader animation to finish
 * (showContent becomes true), then clicks nav-next until closing panel.
 */
async function openClosingPanel(page) {
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

  // Wait for proposal to finish loading
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });

  // Click through sections until nav-next disappears (closing panel)
  let safetyLimit = 10;
  while (safetyLimit-- > 0) {
    await nextBtn.click();
    await page.waitForTimeout(500);
    const stillVisible = await nextBtn.isVisible().catch(() => false);
    if (!stillVisible) break;
  }
}

test.describe('Proposal Respond', () => {
  test.beforeEach(async ({ page }) => {
    // Skip onboarding overlay so buttons are clickable
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('accept button opens confirmation modal', {
    tag: [...PROPOSAL_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Accept button should be visible on the closing panel
    const acceptBtn = page.getByRole('button', { name: /Acepto la propuesta/i });
    await expect(acceptBtn).toBeVisible();

    // Click accept opens confirmation modal (force due to CSS pulse animation)
    await acceptBtn.click({ force: true });
    await expect(page.getByText(/Perfecto/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Confirmar/i })).toBeVisible();
  });

  test('confirming accept calls respond API and shows success state', {
    tag: [...PROPOSAL_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    let respondCalled = false;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        respondCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'accepted' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Click accept → open modal → confirm (force due to CSS pulse animation)
    await page.getByRole('button', { name: /Acepto la propuesta/i }).click({ force: true });
    await page.getByRole('button', { name: /Confirmar/i }).click();

    // Verify success state appears
    await expect(page.getByText('¡Propuesta aceptada!')).toBeVisible({ timeout: 5000 });
    expect(respondCalled).toBe(true);
  });

  test('reject button opens reject modal', {
    tag: [...PROPOSAL_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockSentProposal, status: 'viewed' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Reject button should be visible
    const rejectBtn = page.getByRole('button', { name: /No es el momento/i });
    await expect(rejectBtn).toBeVisible();

    // Click reject opens modal
    await rejectBtn.click();
    await expect(page.getByText(/Lamentamos que no sea el momento/i)).toBeVisible();
  });

  test('accept and reject buttons are hidden after proposal is accepted', {
    tag: [...PROPOSAL_RESPOND, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockSentProposal, status: 'accepted' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Accepted proposal should not show respond buttons
    await expect(page.getByRole('button', { name: /Acepto la propuesta/i })).not.toBeVisible();
    await expect(page.getByText('¡Propuesta aceptada!')).toBeVisible();
  });
});
