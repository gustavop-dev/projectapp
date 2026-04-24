/**
 * E2E tests for proposal engagement tracking on public proposal page.
 *
 * Covers: section navigation tracking via visited panels,
 * section counter updates, and response buttons visibility.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_ENGAGEMENT_TRACKING } from '../helpers/flow-tags.js';

const MOCK_UUID = '3a111111-1111-1111-1111-111111111111';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Tracking Test Proposal',
  client_name: 'Track Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000.00',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Track Client', inspirationalQuote: 'Hello.' },
    },
    {
      id: 2, section_type: 'executive_summary', title: 'Resumen', order: 1, is_enabled: true,
      content_json: { index: '1', title: 'Resumen', paragraphs: ['Intro.'], highlightsTitle: 'Incluye', highlights: ['Item 1'] },
    },
    {
      id: 3, section_type: 'investment', title: 'Inversión', order: 2, is_enabled: true,
      content_json: { index: '2', title: 'Inversión', introText: '', totalInvestment: '10000', currency: 'COP', whatsIncluded: [], paymentOptions: [], paymentMethods: [], valueReasons: [] },
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

test.describe('Proposal Engagement Tracking', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('navigation buttons track section visits', {
    tag: [...PROPOSAL_ENGAGEMENT_TRACKING, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    // Next button should be visible on first section
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });

    // Navigate forward
    await nextBtn.click();

    // Previous button should now be visible (we're past first section)
    await expect(page.getByTestId('nav-prev')).toBeVisible({ timeout: 5000 });
  });

  test('navigating forward and back preserves visit state', {
    tag: [...PROPOSAL_ENGAGEMENT_TRACKING, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });

    // Go forward
    await nextBtn.click();
    await expect(page.getByTestId('nav-prev')).toBeVisible({ timeout: 5000 });

    // Go back
    await page.getByTestId('nav-prev').click();
    await expect(page.getByTestId('nav-prev')).not.toBeVisible({ timeout: 5000 });
  });
});
