/**
 * E2E tests for personalized OG meta tags on proposal pages.
 *
 * Covers: og:title, og:description, and page title include client name
 * and proposal title for WhatsApp/social sharing.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';

const MOCK_UUID = 'bc111111-1111-1111-1111-111111111111';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Propuesta Personalizada Web',
  client_name: 'María García',
  status: 'sent',
  language: 'es',
  total_investment: '8000000',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'María García', inspirationalQuote: '' },
    },
  ],
  requirement_groups: [],
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    return null;
  });
}

test.describe('Proposal OG Meta Personalized', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('page title includes client name after proposal loads', {
    tag: ['@flow:proposal-og-meta-personalized', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });

    // Page title should include client name
    await expect(page).toHaveTitle(/María García/i, { timeout: 5000 });
  });

  test('og:title meta tag contains client name', {
    tag: ['@flow:proposal-og-meta-personalized', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });

    // og:title meta should contain "Propuesta para María García"
    const ogTitle = page.locator('meta[property="og:title"]');
    await expect(ogTitle).toHaveAttribute('content', /María García/i, { timeout: 5000 });
  });

  test('og:description meta tag contains proposal title and client name', {
    tag: ['@flow:proposal-og-meta-personalized', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });

    // og:description should contain both client name and proposal title
    const ogDesc = page.locator('meta[property="og:description"]');
    await expect(ogDesc).toHaveAttribute('content', /María García/i, { timeout: 5000 });
    await expect(ogDesc).toHaveAttribute('content', /Propuesta Personalizada Web/i);
  });
});
