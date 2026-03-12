/**
 * E2E tests for proposal process & methodology section.
 *
 * Covers: 5-step visual pipeline rendering (Discovery → Diseño → Desarrollo → QA → Lanzamiento),
 * step titles and descriptions visibility.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_PROCESS_METHODOLOGY } from '../helpers/flow-tags.js';

const MOCK_UUID = 'process-method-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Process Methodology Proposal',
  client_name: 'Process Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Process Client', inspirationalQuote: 'Hello.' },
    },
    {
      id: 2, section_type: 'process_methodology', title: 'Proceso', order: 1, is_enabled: true,
      content_json: {},
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

test.describe('Proposal Process & Methodology', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
  });

  test('renders 5-step pipeline with correct step titles', {
    tag: [...PROPOSAL_PROCESS_METHODOLOGY, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to process methodology section (section index 1)
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('networkidle');

    // All 5 pipeline steps should be visible (use .first() — desktop + mobile layouts render duplicates)
    await expect(page.getByRole('heading', { name: 'Discovery' }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Diseño UX/UI' }).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Desarrollo' }).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'QA y Testing' }).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Lanzamiento' }).first()).toBeVisible();
  });

  test('pipeline steps show descriptions', {
    tag: [...PROPOSAL_PROCESS_METHODOLOGY, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('networkidle');

    // Check descriptions are rendered (use .first() for same reason)
    await expect(page.getByText(/Investigamos tu negocio/).first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/prototipos interactivos/).first()).toBeVisible();
  });
});
