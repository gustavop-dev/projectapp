/**
 * E2E tests for proposal welcome-back overlay.
 *
 * Covers: welcome-back overlay for returning clients, continue and
 * start-from-beginning buttons, localStorage-based progress detection.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_WELCOME_BACK } from '../helpers/flow-tags.js';

const MOCK_UUID = 'welcome-back-uuid-1234-5678-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Welcome Back Proposal',
  client_name: 'Maria Test',
  status: 'sent',
  language: 'es',
  total_investment: '10000000',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Maria Test', inspirationalQuote: 'Hello.' },
    },
    {
      id: 2, section_type: 'executive_summary', title: 'Resumen', order: 1, is_enabled: true,
      content_json: { index: '1', title: 'Resumen', paragraphs: ['Summary text.'], highlightsTitle: 'Highlights', highlights: ['Item'] },
    },
    {
      id: 3, section_type: 'timeline', title: 'Cronograma', order: 2, is_enabled: true,
      content_json: { index: '2', title: 'Cronograma', totalDuration: '8 semanas', phases: [] },
    },
  ],
  requirement_groups: [],
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    if (apiPath === `proposals/${MOCK_UUID}/track/` && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    return null;
  });
}

test.describe('Proposal Welcome Back', () => {
  test('navigating sections persists progress to localStorage', {
    tag: [...PROPOSAL_WELCOME_BACK, '@role:client'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate forward to trigger progress persistence
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible({ timeout: 15000 });
    await nextBtn.click();
    await page.waitForLoadState('networkidle');

    // Check that progress was saved in localStorage
    const saved = await page.evaluate((uuid) => {
      return localStorage.getItem(`proposal-${uuid}-progress`);
    }, MOCK_UUID);

    expect(saved).not.toBeNull();
    const data = JSON.parse(saved);
    expect(data.sectionIndex).toBe(1);
    expect(data.clientName).toBe('Maria Test');
  });

  test('welcome-back does not appear on first visit', {
    tag: [...PROPOSAL_WELCOME_BACK, '@role:client'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);

    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for page to render, then check no welcome-back
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Bienvenido de nuevo')).not.toBeVisible();
  });
});
