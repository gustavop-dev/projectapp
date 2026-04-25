/**
 * E2E tests for proposal rejection with optional reason.
 *
 * Covers: rejection reason is optional, nudge text visibility,
 * and ability to reject without selecting a reason.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_REJECTION_OPTIONAL_REASON } from '../helpers/flow-tags.js';

const MOCK_UUID = 'b5111111-1111-1111-1111-111111111111';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Rejection Test Proposal',
  client_name: 'Test Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Test Client', inspirationalQuote: 'Hello.' },
    },
    {
      id: 2, section_type: 'next_steps', title: 'Próximos pasos', order: 1, is_enabled: true,
      content_json: { index: '1', title: 'Próximos pasos' },
    },
  ],
  requirement_groups: [],
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    if (apiPath === `proposals/${MOCK_UUID}/respond/` && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) };
    }
    return null;
  });
}

test.describe('Proposal Rejection Optional Reason', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('reject modal shows optional reason label and nudge text', {
    tag: [...PROPOSAL_REJECTION_OPTIONAL_REASON, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Navigate to last section (closing panel)
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();

    // Click reject link
    const rejectLink = page.getByRole('button', { name: /No es el momento/i });
    await expect(rejectLink).toBeVisible({ timeout: 10000 });
    await rejectLink.click();

    // Reject modal should show optional label and nudge
    await expect(page.getByText(/opcional y confidencial/)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Motivo \(opcional\)/)).toBeVisible();
  });

  test('"Confirmar rechazo" button is enabled without selecting a reason', {
    tag: [...PROPOSAL_REJECTION_OPTIONAL_REASON, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();

    const rejectLink = page.getByRole('button', { name: /No es el momento/i });
    await expect(rejectLink).toBeVisible({ timeout: 10000 });
    await rejectLink.click();

    // "Confirmar rechazo" button should be enabled (not disabled) without a reason
    const confirmBtn = page.getByRole('button', { name: /Confirmar rechazo/i });
    await expect(confirmBtn).toBeVisible({ timeout: 5000 });
    await expect(confirmBtn).toBeEnabled();
  });
});
