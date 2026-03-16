/**
 * E2E tests for mobile onboarding swipe carousel.
 *
 * Covers: onboarding carousel renders on mobile viewport,
 * swipe hint text visible, progress dots visible, step navigation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';

const MOCK_UUID = 'onb-mobile-uuid-1234-abcdef';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Onboarding Mobile Test',
  client_name: 'Mobile Client',
  status: 'sent',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Mobile Client', inspirationalQuote: '' },
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

test.describe('Proposal Onboarding Mobile Swipe', () => {
  test.use({ viewport: { width: 375, height: 812 } });

  test.beforeEach(async ({ page }) => {
    // Clear any residual localStorage that might block onboarding
    await page.addInitScript((_uuid) => {
      localStorage.removeItem('proposal_onboarding_seen');
      localStorage.removeItem(`proposal-${_uuid}-progress`);
      localStorage.removeItem(`proposal-${_uuid}-viewMode`);
    }, MOCK_UUID);
  });

  test('mobile onboarding tooltip renders with first step and navigation buttons', {
    tag: ['@flow:proposal-onboarding-mobile-swipe', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    // Onboarding tooltip should appear with first step on mobile too
    await expect(page.getByRole('heading', { name: 'Modo claro y oscuro' })).toBeVisible({ timeout: 15000 });

    // "Siguiente" button should be visible
    await expect(page.getByRole('button', { name: /Siguiente/i })).toBeVisible();
  });

  test('tapping "Siguiente" advances to next onboarding step', {
    tag: ['@flow:proposal-onboarding-mobile-swipe', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    // First step
    await expect(page.getByRole('heading', { name: 'Modo claro y oscuro' })).toBeVisible({ timeout: 15000 });

    // Click "Siguiente" to advance
    await page.getByRole('button', { name: /Siguiente/i }).click();

    // Second step should show index section text
    await expect(page.getByText(/Índice de secciones/i)).toBeVisible({ timeout: 3000 });
  });

  test('tapping "Omitir" dismisses onboarding', {
    tag: ['@flow:proposal-onboarding-mobile-swipe', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByRole('heading', { name: 'Modo claro y oscuro' })).toBeVisible({ timeout: 15000 });

    // Click "Omitir" to dismiss
    await page.getByRole('button', { name: /Omitir/i }).click();

    // Onboarding should disappear
    await expect(page.getByRole('heading', { name: 'Modo claro y oscuro' })).not.toBeVisible({ timeout: 3000 });
  });
});
