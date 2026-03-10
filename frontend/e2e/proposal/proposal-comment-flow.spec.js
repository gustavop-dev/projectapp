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

test.describe('Proposal Comment from Closing Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('comment button opens modal with textarea', {
    tag: [...PROPOSAL_COMMENT_FROM_CLOSING, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockSentProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    await page.getByRole('button', { name: /Tengo comentarios por escrito/i }).click();
    await expect(page.getByText(/Tus comentarios nos ayudan/i)).toBeVisible();
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

    await page.getByRole('button', { name: /Tengo comentarios por escrito/i }).click();
    await expect(page.getByText(/Tus comentarios nos ayudan/i)).toBeVisible();

    const sendBtn = page.getByRole('button', { name: /Enviar mensaje/i });
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

    await page.getByRole('button', { name: /Tengo comentarios por escrito/i }).click();
    await expect(page.getByText(/Tus comentarios nos ayudan/i)).toBeVisible();

    await page.locator('textarea').fill('Me gustaría saber más sobre los tiempos de entrega.');

    const [commentResponse] = await Promise.all([
      page.waitForResponse(r => r.url().includes(`proposals/${MOCK_UUID}/comment/`)),
      page.getByRole('button', { name: /Enviar mensaje/i }).click(),
    ]);
    await commentResponse.finished();

    await expect(page.getByText(/Mensaje enviado/i)).toBeVisible({ timeout: 5000 });
    expect(commentCalled).toBe(true);
  });
});
