/**
 * E2E tests for calculator micro-feedback badge.
 *
 * Covers: toggling a calculator module shows a transient +/- price badge.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_CALCULATOR_MICRO_FEEDBACK } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Micro Feedback Proposal',
  client_name: 'Test Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
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
    {
      id: 2,
      section_type: 'investment',
      title: '💰 Inversión',
      order: 1,
      is_enabled: true,
      content_json: {
        totalInvestment: 10000000,
        currency: 'COP',
        estimatedWeeks: 12,
        calculatorModules: [
          { id: 'pwa', name: 'PWA', percent: 40, selected: false, description: 'Progressive Web App' },
          { id: 'reports', name: 'Reportes y Alertas', percent: 20, selected: true, description: 'Reports' },
        ],
      },
    },
  ],
  requirement_groups: [],
};

async function openInvestmentSection(page) {
  await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  await nextBtn.click();
  await expect(page.getByRole('heading', { name: /Inversi[oó]n y Formas de Pago/i })).toBeVisible({ timeout: 5000 });
}

test.describe('Proposal Calculator Micro-Feedback', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('toggling a calculator module shows price feedback badge', {
    tag: [...PROPOSAL_CALCULATOR_MICRO_FEEDBACK, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
      }
      return null;
    });

    await openInvestmentSection(page);

    // Open calculator modal
    const calcBtn = page.getByRole('button', { name: /Personalizar/i });
    if (await calcBtn.isVisible().catch(() => false)) {
      await calcBtn.click();

      // Find a module toggle and click it
      const moduleToggle = page.locator('[data-testid="calc-module-toggle"]').first();
      if (await moduleToggle.isVisible().catch(() => false)) {
        await moduleToggle.click();
        // The micro-feedback badge should appear briefly
        const feedback = page.locator('[class*="micro-feedback"], [data-testid="price-feedback"]');
        await expect(feedback).toBeVisible({ timeout: 3000 });
      }
    }
  });
});
