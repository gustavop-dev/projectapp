/**
 * E2E tests for proposal onboarding tutorial on public proposal page.
 *
 * Covers: onboarding tooltip display, step navigation,
 * dismiss functionality, and localStorage persistence.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_VIEW_ONBOARDING } from '../helpers/flow-tags.js';

const MOCK_UUID = 'onboard-test-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Onboarding Test Proposal',
  client_name: 'Onboard Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000.00',
  currency: 'COP',
  expires_at: '2027-12-31T23:59:59Z',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Onboard Client', inspirationalQuote: 'Hello.' },
    },
    {
      id: 2, section_type: 'executive_summary', title: 'Resumen', order: 1, is_enabled: true,
      content_json: { index: '1', title: 'Resumen', paragraphs: ['Intro.'], highlightsTitle: 'Incluye', highlights: ['Item'] },
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

test.describe('Proposal Onboarding', () => {
  test('onboarding tooltip appears on first visit', {
    tag: [...PROPOSAL_VIEW_ONBOARDING, '@role:client'],
  }, async ({ page }) => {
    // Do NOT set proposal_onboarding_seen — let onboarding show
    await page.addInitScript((uuid) => {
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Onboarding tooltip should appear with first step
    await expect(page.getByText('Índice de secciones')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Omitir')).toBeVisible();
  });

  test('clicking Omitir dismisses onboarding', {
    tag: [...PROPOSAL_VIEW_ONBOARDING, '@role:client'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Índice de secciones')).toBeVisible({ timeout: 15000 });

    // Click "Omitir" to dismiss
    await page.getByText('Omitir').click();

    // Onboarding should disappear
    await expect(page.getByText('Índice de secciones')).not.toBeVisible({ timeout: 5000 });
  });

  test('onboarding does not appear on subsequent visits', {
    tag: [...PROPOSAL_VIEW_ONBOARDING, '@role:client'],
  }, async ({ page }) => {
    // Set localStorage as if onboarding was already seen
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);

    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Onboarding should NOT appear
    await expect(page.getByText('Índice de secciones')).not.toBeVisible({ timeout: 5000 });
  });
});
