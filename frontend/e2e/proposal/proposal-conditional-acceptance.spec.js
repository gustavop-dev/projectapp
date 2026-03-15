/**
 * E2E tests for conditional acceptance ("Acepto, pero...").
 *
 * Covers: accept confirmation modal shows optional condition textarea,
 * accepting with a condition sends it in the API payload,
 * accepting without a condition still works normally.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CONDITIONAL_ACCEPTANCE } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockSentProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Conditional Accept Proposal',
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
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  let safetyLimit = 15;
  while (safetyLimit-- > 0) {
    await nextBtn.click();
    await page.waitForTimeout(500);
    const stillVisible = await nextBtn.isVisible().catch(() => false);
    if (!stillVisible) break;
  }
}

test.describe('Proposal Conditional Acceptance', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('accept modal shows optional condition textarea', {
    tag: [...PROPOSAL_CONDITIONAL_ACCEPTANCE, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Open accept modal
    await page.getByRole('button', { name: /Acepto la propuesta/i }).click({ force: true });

    // Condition textarea visible with correct label
    await expect(page.getByText(/¿Aceptas con alguna condición/i)).toBeVisible();
    const conditionTextarea = page.getByPlaceholder(/Acepto, pero necesito/i);
    await expect(conditionTextarea).toBeVisible();
  });

  test('accepting with a condition sends condition in API payload', {
    tag: [...PROPOSAL_CONDITIONAL_ACCEPTANCE, '@role:guest'],
  }, async ({ page }) => {
    let respondPayload = null;

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        respondPayload = JSON.parse(route.request().postData() || '{}');
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'accepted' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Open accept modal
    await page.getByRole('button', { name: /Acepto la propuesta/i }).click({ force: true });

    // Type a condition
    const conditionTextarea = page.getByPlaceholder(/Acepto, pero necesito/i);
    await conditionTextarea.fill('Necesito que se incluya soporte por 6 meses');

    // Confirm acceptance
    await page.getByRole('button', { name: /Confirmar/i }).click();

    // Verify success state
    await expect(page.getByText('¡Propuesta aceptada!')).toBeVisible({ timeout: 5000 });
    expect(respondPayload).toBeTruthy();
    expect(respondPayload.condition).toBe('Necesito que se incluya soporte por 6 meses');
  });

  test('accepting without a condition works normally', {
    tag: [...PROPOSAL_CONDITIONAL_ACCEPTANCE, '@role:guest'],
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

    // Open accept modal and confirm without typing condition
    await page.getByRole('button', { name: /Acepto la propuesta/i }).click({ force: true });
    await page.getByRole('button', { name: /Confirmar/i }).click();

    await expect(page.getByText('¡Propuesta aceptada!')).toBeVisible({ timeout: 5000 });
    expect(respondCalled).toBe(true);
  });
});
