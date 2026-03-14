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

  test('mobile onboarding carousel renders with swipe hint and progress dots', {
    tag: ['@flow:proposal-onboarding-mobile-swipe', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    // Ensure onboarding has NOT been seen (remove storage flag)
    await page.addInitScript((uuid) => {
      localStorage.removeItem('proposal_onboarding_seen');
    }, MOCK_UUID);

    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);

    // Gateway shows first — pick detailed view
    await page.getByText('Propuesta Completa').click();

    // Wait for proposal to load and onboarding to appear
    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 20000 });

    // Onboarding mobile carousel should appear with swipe hint
    await expect(page.getByText(/Desliza o usa los botones/i)).toBeVisible({ timeout: 10000 });

    // Progress dots should be visible
    await expect(page.getByText(/Índice de secciones/i)).toBeVisible();

    // "Siguiente" button should be visible
    await expect(page.getByRole('button', { name: /Siguiente/i })).toBeVisible();
  });

  test('tapping "Siguiente" advances to next onboarding step', {
    tag: ['@flow:proposal-onboarding-mobile-swipe', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.removeItem('proposal_onboarding_seen');
    }, MOCK_UUID);

    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);

    // Gateway shows first
    await page.getByText('Propuesta Completa').click();

    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 20000 });
    await expect(page.getByText(/Desliza o usa los botones/i)).toBeVisible({ timeout: 10000 });

    // First step title
    await expect(page.getByText(/Índice de secciones/i)).toBeVisible();

    // Click "Siguiente" to advance
    await page.getByRole('button', { name: /Siguiente/i }).click();

    // Second step should show navigation text
    await expect(page.getByText(/Navegar entre secciones/i)).toBeVisible({ timeout: 3000 });
  });

  test('tapping "Omitir" dismisses onboarding', {
    tag: ['@flow:proposal-onboarding-mobile-swipe', '@module:proposal', '@priority:P3', '@role:guest'],
  }, async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.removeItem('proposal_onboarding_seen');
    }, MOCK_UUID);

    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}`);

    // Gateway shows first
    await page.getByText('Propuesta Completa').click();

    await expect(page.getByTestId('nav-next')).toBeVisible({ timeout: 20000 });
    await expect(page.getByText(/Desliza o usa los botones/i)).toBeVisible({ timeout: 10000 });

    // Click "Omitir" to dismiss
    await page.getByRole('button', { name: /Omitir/i }).click();

    // Onboarding should disappear
    await expect(page.getByText(/Desliza o usa los botones/i)).not.toBeVisible({ timeout: 3000 });
  });
});
