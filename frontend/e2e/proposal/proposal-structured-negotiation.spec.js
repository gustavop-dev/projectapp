/**
 * E2E tests for the structured negotiation modal.
 *
 * Covers: clicking "Necesito ajustes" opens modal with structured checkboxes,
 * tab toggle between adjust/comment, and sending negotiation request.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_STRUCTURED_NEGOTIATION } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockSentProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Negotiation Proposal',
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

test.describe('Proposal Structured Negotiation Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
  });

  test('negotiate button opens modal with structured checkboxes', {
    tag: [...PROPOSAL_STRUCTURED_NEGOTIATION, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Click negotiate button
    const negotiateBtn = page.getByRole('button', { name: /Necesito ajustes/i });
    await expect(negotiateBtn).toBeVisible();
    await negotiateBtn.click();

    // Modal opens with structured checkboxes
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible({ timeout: 3000 });
    await expect(page.getByText('Reducir alcance / módulos')).toBeVisible();
    await expect(page.getByText('Ajustar timeline')).toBeVisible();
    await expect(page.getByText('Explorar precio diferente')).toBeVisible();
    await expect(page.getByText('Cambiar prioridades')).toBeVisible();
    await expect(page.getByText('Otro ajuste')).toBeVisible();
  });

  test('negotiate modal has tab toggle between adjust and comment', {
    tag: [...PROPOSAL_STRUCTURED_NEGOTIATION, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    await page.getByRole('button', { name: /Necesito ajustes/i }).click();
    await page.waitForTimeout(500);

    // Both tabs should be visible inside the modal
    const modal = page.locator('.fixed.inset-0').filter({ hasText: /negociemos alcance/i });
    const adjustTab = modal.getByRole('button', { name: /Necesito ajustes/i });
    const commentTab = modal.getByRole('button', { name: /comentarios por escrito/i });
    await expect(adjustTab).toBeVisible();
    await expect(commentTab).toBeVisible();

    // Switch to comment tab
    await commentTab.click();
    await page.waitForTimeout(300);

    // Cancel button visible on both tabs
    await expect(modal.getByRole('button', { name: /Cancelar/i })).toBeVisible();
  });

  test('selecting checkboxes and sending negotiation calls API', {
    tag: [...PROPOSAL_STRUCTURED_NEGOTIATION, '@role:guest'],
  }, async ({ page }) => {
    let respondPayload = null;

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        respondPayload = JSON.parse(route.request().postData() || '{}');
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'negotiating' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    await page.getByRole('button', { name: /Necesito ajustes/i }).click();
    await page.waitForTimeout(500);

    // Select two checkboxes
    await page.getByText('Ajustar timeline').click();
    await page.getByText('Explorar precio diferente').click();

    // Submit
    const sendBtn = page.getByRole('button', { name: /Enviar solicitud de ajustes/i });
    await expect(sendBtn).toBeEnabled();
    await sendBtn.click();

    // Verify success state
    await expect(page.getByText(/¡Solicitud recibida!/i)).toBeVisible({ timeout: 5000 });
  });
});
