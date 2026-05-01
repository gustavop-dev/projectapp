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
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  let safetyLimit = 15;
  while (safetyLimit-- > 0) {
    await nextBtn.click();
    await page.waitForLoadState('domcontentloaded');
    const stillVisible = await nextBtn.isVisible().catch(() => false);
    if (!stillVisible) break;
  }

  // Wait for slide transition to finish so buttons become stable
  await page.locator('[data-section-type="proposal_closing"]').waitFor({ state: 'visible', timeout: 5000 });
}

test.describe('Proposal Structured Negotiation Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('negotiate button opens structured negotiation modal', {
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

    // Modal opens with title
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible({ timeout: 3000 });
  });

  test('negotiation modal renders all structured checkbox options', {
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
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible({ timeout: 3000 });

    // All structured checkbox options render
    await expect(page.getByText('El presupuesto es alto para este momento')).toBeVisible();
    await expect(page.getByText('Necesito ajustar el alcance o quitar módulos')).toBeVisible();
    await expect(page.getByText('Los tiempos de entrega no me funcionan')).toBeVisible();
    await expect(page.getByText('Quiero agregar o cambiar funcionalidades')).toBeVisible();
    await expect(page.getByText('Necesito aprobación de otro decisor')).toBeVisible();
    await expect(page.getByText('Otro ajuste')).toBeVisible();
  });

  test('closing panel has separate negotiate and comment modals', {
    tag: [...PROPOSAL_STRUCTURED_NEGOTIATION, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Open negotiate modal and verify structure
    await page.getByRole('button', { name: /Necesito ajustes/i }).click();
    const negotiateModal = page.locator('.fixed.inset-0').filter({ hasText: /negociemos alcance/i });
    await expect(negotiateModal).toBeVisible({ timeout: 5000 });
    await expect(negotiateModal.getByRole('button', { name: /Cancelar/i })).toBeVisible();

    // Close negotiate modal
    await negotiateModal.getByRole('button', { name: /Cancelar/i }).click();
    await expect(negotiateModal).not.toBeVisible({ timeout: 3000 });

    // Open comment modal separately and verify structure
    await page.getByRole('button', { name: /Tengo comentarios/i }).click();
    const commentModal = page.locator('.fixed.inset-0').filter({ hasText: /Tengo comentarios/i });
    await expect(commentModal).toBeVisible({ timeout: 3000 });
    await expect(commentModal.locator('textarea')).toBeVisible();
    await expect(commentModal.getByRole('button', { name: /Cancelar/i })).toBeVisible();
  });

  test('selecting checkboxes and sending negotiation calls API', {
    tag: [...PROPOSAL_STRUCTURED_NEGOTIATION, '@role:guest'],
  }, async ({ page }) => {
    let _respondPayload = null;

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        _respondPayload = JSON.parse(route.request().postData() || '{}');
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'negotiating' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    await page.getByRole('button', { name: /Necesito ajustes/i }).click();
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible({ timeout: 5000 });

    // Select two checkboxes
    await page.getByText('Los tiempos de entrega no me funcionan').click();
    await page.getByText('El presupuesto es alto para este momento').click();

    // Submit
    const sendBtn = page.getByRole('button', { name: /Enviar 2 ajustes/i });
    await expect(sendBtn).toBeEnabled();
    await sendBtn.click();

    // Verify success state
    await expect(page.getByText(/¡Solicitud recibida!/i)).toBeVisible({ timeout: 5000 });
  });
});
