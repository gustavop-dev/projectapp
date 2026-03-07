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
  sections: [],
  requirement_groups: [],
};

/**
 * Helper: navigate to the last panel (proposal_closing) which contains
 * the accept/reject buttons. Since the mock has 0 sections, displayPanels
 * will have only 1 panel (proposal_closing), so we land on it directly.
 */
async function openClosingPanel(page) {
  await page.goto(`/proposal/${MOCK_UUID}`);
  await page.waitForLoadState('networkidle');

  // Navigate through all panels to reach the closing panel
  const nextBtn = page.getByTestId('nav-next');
  let safetyLimit = 10;
  while (await nextBtn.isVisible() && safetyLimit-- > 0) {
    await nextBtn.click();
    await page.waitForTimeout(300);
  }
}

test.describe('Proposal Respond', () => {
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

    // Click accept opens confirmation modal
    await acceptBtn.click();
    await expect(page.getByText('¿Confirmar aceptación?')).toBeVisible();
    await expect(page.getByRole('button', { name: /Sí, acepto/i })).toBeVisible();
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

    // Click accept → open modal → confirm
    await page.getByRole('button', { name: /Acepto la propuesta/i }).click();
    await page.getByRole('button', { name: /Sí, acepto/i }).click();

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
    const rejectBtn = page.getByRole('button', { name: /Rechazar propuesta/i });
    await expect(rejectBtn).toBeVisible();

    // Click reject opens modal
    await rejectBtn.click();
    await expect(page.getByText('Lamentamos que no sea el momento')).toBeVisible();
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
