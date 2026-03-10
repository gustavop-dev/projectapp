/**
 * E2E tests for smart rejection recovery cards in the proposal closing panel.
 *
 * Covers: rejecting with different reasons triggers different recovery cards,
 * each with context-specific CTA (WhatsApp, schedule reminder, farewell).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_REJECTION_SMART_RECOVERY } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockSentProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Recovery Test Proposal',
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

async function openClosingPanel(page) {
  await page.goto(`/proposal/${MOCK_UUID}`);
  await expect(page.locator('.proposal-wrapper')).toBeVisible({ timeout: 15000 });

  const nextBtn = page.getByTestId('nav-next');
  let safetyLimit = 10;
  while (safetyLimit-- > 0) {
    const isVisible = await nextBtn.isVisible({ timeout: 500 }).catch(() => false);
    if (!isVisible) break;
    await nextBtn.click();
    await expect(page.locator('.panel-container')).toBeVisible();
  }
}

async function rejectWithReason(page, reason) {
  await page.getByRole('button', { name: /No me interesa por ahora/i }).click();
  await expect(page.getByText(/Lamentamos que no sea el momento/i)).toBeVisible();

  // Select reason inside the reject modal (Teleport to body)
  const modal = page.locator('.fixed').filter({ hasText: 'Confirmar rechazo' });
  if (reason) {
    const selectEl = modal.locator('select');
    await expect(selectEl).toBeVisible();
    await selectEl.selectOption(reason);
    // Wait for Vue reactivity to propagate the selected value
    await expect(selectEl).toHaveValue(reason);
  }

  const confirmBtn = modal.getByRole('button', { name: /Confirmar rechazo/i });
  const [respondResponse] = await Promise.all([
    page.waitForResponse(r => r.url().includes(`proposals/${MOCK_UUID}/respond/`)),
    confirmBtn.click(),
  ]);
  await respondResponse.finished();
}

function buildMockHandler(respondStatus = 'rejected') {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
    }
    if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: respondStatus }) };
    }
    return null;
  };
}

test.describe('Proposal Rejection Smart Recovery', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('reject modal opens with reason select and confirm button', {
    tag: [...PROPOSAL_REJECTION_SMART_RECOVERY, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await openClosingPanel(page);

    await page.getByRole('button', { name: /No me interesa por ahora/i }).click();
    await expect(page.getByText(/Lamentamos que no sea el momento/i)).toBeVisible();

    // Verify modal has reason select and confirm button
    const modal = page.locator('.fixed').filter({ hasText: 'Confirmar rechazo' });
    await expect(modal.locator('select')).toBeVisible();
    await expect(modal.getByRole('button', { name: /Confirmar rechazo/i })).toBeVisible();
  });

  test('rejecting with "No es el momento" shows schedule reminder card', {
    tag: [...PROPOSAL_REJECTION_SMART_RECOVERY, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await openClosingPanel(page);
    await rejectWithReason(page, 'No es el momento');

    await expect(page.getByText(/recordamos más adelante/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole('button', { name: /Recordármelo en 3 meses/i })).toBeVisible();
  });

  test('rejecting with "Encontré otra opción" shows farewell card', {
    tag: [...PROPOSAL_REJECTION_SMART_RECOVERY, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await openClosingPanel(page);
    await rejectWithReason(page, 'Encontré otra opción');

    await expect(page.getByText(/Gracias por tu honestidad/i)).toBeVisible({ timeout: 5000 });
  });

  test('rejecting without reason shows rejection message', {
    tag: [...PROPOSAL_REJECTION_SMART_RECOVERY, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await openClosingPanel(page);
    await rejectWithReason(page, null);

    // After rejection, the rejection status message should be visible
    await expect(page.getByText(/Propuesta rechazada/i)).toBeVisible({ timeout: 5000 });
  });
});
