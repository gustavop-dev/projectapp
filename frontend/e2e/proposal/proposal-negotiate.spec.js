/**
 * E2E tests for client negotiating a proposal ("Aceptar con cambios").
 *
 * Covers: opening negotiate modal, submitting with required comment,
 * verifying API call with action=negotiating, success state display.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_NEGOTIATE } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockSentProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Negotiate Test Proposal',
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

test.describe('Proposal Negotiate (Accept with Changes)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('negotiate button opens modal with textarea', {
    tag: [...PROPOSAL_NEGOTIATE, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    const negotiateBtn = page.getByRole('button', { name: /Aceptar con cambios/i });
    await expect(negotiateBtn).toBeVisible();

    await negotiateBtn.click();
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible();
    await expect(page.locator('textarea')).toBeVisible();
  });

  test('negotiate submit is disabled when comment is empty', {
    tag: [...PROPOSAL_NEGOTIATE, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    await page.getByRole('button', { name: /Aceptar con cambios/i }).click();
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible();

    const submitBtn = page.getByRole('button', { name: /Enviar solicitud de ajustes/i });
    await expect(submitBtn).toBeDisabled();
  });

  test('submitting negotiate calls respond API and shows success state', {
    tag: [...PROPOSAL_NEGOTIATE, '@role:guest'],
  }, async ({ page }) => {
    let respondCalled = false;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/respond/`) {
        respondCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'negotiating' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    await page.getByRole('button', { name: /Aceptar con cambios/i }).click();
    await expect(page.getByText(/negociemos alcance/i)).toBeVisible();

    await page.locator('textarea').fill('Me gustaría reducir el número de módulos y ajustar el timeline.');

    const [respondResponse] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`proposals/${MOCK_UUID}/respond/`)),
      page.getByRole('button', { name: /Enviar solicitud de ajustes/i }).click(),
    ]);
    await respondResponse.finished();

    await expect(page.getByText(/Solicitud recibida/i)).toBeVisible({ timeout: 5000 });
    expect(respondCalled).toBe(true);
  });

  test('negotiate buttons are hidden after proposal is already negotiating', {
    tag: [...PROPOSAL_NEGOTIATE, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockSentProposal, status: 'negotiating' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    await expect(page.getByRole('button', { name: /Acepto la propuesta/i })).not.toBeVisible();
    await expect(page.getByText(/Solicitud recibida/i)).toBeVisible();
  });
});
