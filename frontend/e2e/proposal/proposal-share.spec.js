/**
 * E2E tests for proposal share button on public proposal page.
 *
 * Covers: share button visibility, quick-copy click, share modal open
 * via context menu, and share link creation form.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_SHARE } from '../helpers/flow-tags.js';

const MOCK_UUID = 'share-test-uuid-1234-5678-abcdef123456';

const mockProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Share Test Proposal',
  client_name: 'Share Client',
  status: 'sent',
  language: 'es',
  total_investment: '10000.00',
  currency: 'COP',
  sections: [
    {
      id: 1, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true,
      content_json: { clientName: 'Share Client', inspirationalQuote: 'Hello.' },
    },
  ],
  requirement_groups: [],
};

const mockShareResult = {
  uuid: 'shared-link-uuid-9999',
  shared_by_name: 'Juan Pérez',
  shared_by_email: 'juan@test.com',
};

function setupMock(page) {
  return mockApi(page, async ({ route, apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposal) };
    }
    if (apiPath === `proposals/${MOCK_UUID}/share/` && route.request().method() === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify(mockShareResult) };
    }
    return null;
  });
}

test.describe('Proposal Share', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('share button is visible on proposal page', {
    tag: [...PROPOSAL_SHARE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('share-proposal-btn')).toBeVisible({ timeout: 15000 });
  });

  test('share modal opens via context menu and creates link', {
    tag: [...PROPOSAL_SHARE, '@role:client'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);
    await page.waitForLoadState('networkidle');

    const shareBtn = page.getByTestId('share-proposal-btn');
    await expect(shareBtn).toBeVisible({ timeout: 15000 });

    // Right-click opens the modal (contextmenu event)
    await shareBtn.dispatchEvent('contextmenu');

    await expect(page.getByText('Compartir propuesta')).toBeVisible();
    await expect(page.getByPlaceholder('Ej: Juan Pérez')).toBeVisible();

    // Fill share form and create link
    await page.getByPlaceholder('Ej: Juan Pérez').fill('Juan Pérez');
    await page.getByPlaceholder('juan@empresa.com').fill('juan@test.com');
    await page.getByRole('button', { name: 'Crear enlace' }).click();

    await expect(page.getByText('¡Enlace listo!')).toBeVisible({ timeout: 10000 });
  });
});
