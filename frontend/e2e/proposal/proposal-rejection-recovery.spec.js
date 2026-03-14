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
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

  // Wait for proposal to finish loading — nav-next appears once content is ready
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });

  // Click through sections until nav-next disappears (we're on the closing panel)
  let safetyLimit = 10;
  while (safetyLimit-- > 0) {
    await nextBtn.click();
    // Wait for section transition, then check if next is still available
    await page.waitForTimeout(500);
    const stillVisible = await nextBtn.isVisible().catch(() => false);
    if (!stillVisible) break;
  }

  // Confirm we reached the closing panel
  await expect(page.getByRole('button', { name: /No es el momento/i })).toBeVisible({ timeout: 5000 });
}

async function rejectWithReason(page, reason) {
  await page.getByRole('button', { name: /No es el momento/i }).click();
  await expect(page.getByText(/Lamentamos que no sea el momento/i)).toBeVisible();

  // Select reason inside the reject modal (Teleport to body)
  if (reason) {
    // quality: allow-fragile-selector (rejection modal select has no testid, only one select in the modal)
    const selectEl = page.locator('select').first();
    await expect(selectEl).toBeVisible({ timeout: 3000 });
    await selectEl.selectOption(reason);
    await expect(selectEl).toHaveValue(reason);
  }

  const confirmBtn = page.getByRole('button', { name: /Confirmar rechazo/i });
  const [respondResponse] = await Promise.all([
    page.waitForResponse(r => r.url().includes(`proposals/${MOCK_UUID}/respond/`), { timeout: 10000 }),
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
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('reject modal opens with reason select and confirm button', {
    tag: [...PROPOSAL_REJECTION_SMART_RECOVERY, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await openClosingPanel(page);

    await page.getByRole('button', { name: /No es el momento/i }).click();
    await expect(page.getByText(/Lamentamos que no sea el momento/i)).toBeVisible();

    // quality: allow-fragile-selector (rejection modal select has no testid)
    await expect(page.locator('select').first()).toBeVisible({ timeout: 3000 });
    await expect(page.getByRole('button', { name: /Confirmar rechazo/i })).toBeVisible();
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
