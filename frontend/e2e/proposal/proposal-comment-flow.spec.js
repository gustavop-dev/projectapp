/**
 * E2E tests for client submitting a comment from the proposal closing panel.
 *
 * Covers: opening comment modal, typing message, submitting via API,
 * verifying success feedback, empty comment disabled state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_COMMENT_FROM_CLOSING } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockSentProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Comment Flow Test',
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

test.describe('Proposal Comment from Closing Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('comment tab opens textarea inside negotiate modal', {
    tag: [...PROPOSAL_COMMENT_FROM_CLOSING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Open negotiate modal then switch to comment tab
    await page.getByRole('button', { name: /Necesito ajustes|I need adjustments/i }).click();
    await page.getByRole('button', { name: /Tengo comentarios por escrito|I have written comments/i }).click();
    await expect(page.locator('textarea')).toBeVisible();
  });

  test('comment submit is disabled when textarea is empty', {
    tag: [...PROPOSAL_COMMENT_FROM_CLOSING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Open negotiate modal then switch to comment tab
    await page.getByRole('button', { name: /Necesito ajustes|I need adjustments/i }).click();
    await page.getByRole('button', { name: /Tengo comentarios por escrito|I have written comments/i }).click();

    const sendBtn = page.getByRole('button', { name: /Enviar mensaje|Send message/i });
    await expect(sendBtn).toBeDisabled();
  });

  test('submitting comment calls API and shows success feedback', {
    tag: [...PROPOSAL_COMMENT_FROM_CLOSING, '@role:guest'],
  }, async ({ page }) => {
    let commentCalled = false;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      if (apiPath === `proposals/${MOCK_UUID}/comment/`) {
        commentCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Open negotiate modal then switch to comment tab
    await page.getByRole('button', { name: /Necesito ajustes|I need adjustments/i }).click();
    await page.getByRole('button', { name: /Tengo comentarios por escrito|I have written comments/i }).click();

    await page.locator('textarea').fill('Me gustaría saber más sobre los tiempos de entrega.');

    const [commentResponse] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`proposals/${MOCK_UUID}/comment/`)),
      page.getByRole('button', { name: /Enviar mensaje|Send message/i }).click(),
    ]);
    await commentResponse.finished();

    await expect(page.getByText(/Mensaje enviado|Message sent/i)).toBeVisible({ timeout: 5000 });
    expect(commentCalled).toBe(true);
  });
});
