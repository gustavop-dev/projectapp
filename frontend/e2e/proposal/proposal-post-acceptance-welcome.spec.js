/**
 * E2E tests for the post-acceptance welcome kit.
 *
 * Covers: after acceptance, the closing panel shows PDF download link,
 * onboarding timeline (3 steps), and PM WhatsApp contact button.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_POST_ACCEPTANCE_WELCOME } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

const mockAcceptedProposal = {
  id: 1,
  uuid: MOCK_UUID,
  title: 'Welcome Kit Proposal',
  client_name: 'Test Client',
  client_phone: '573001234567',
  status: 'accepted',
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
  const nextBtn = page.getByTestId('nav-next');
  await expect(nextBtn).toBeVisible({ timeout: 15000 });
  let safetyLimit = 15;
  while (safetyLimit-- > 0) {
    await nextBtn.click();
    await page.waitForTimeout(500);
    const stillVisible = await nextBtn.isVisible().catch(() => false);
    if (!stillVisible) break;
  }
}

test.describe('Proposal Post-Acceptance Welcome Kit', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
      localStorage.setItem(`proposal-${uuid}-viewMode`, 'detailed');
    }, MOCK_UUID);
  });

  test('accepted proposal shows celebration and welcome kit elements', {
    tag: [...PROPOSAL_POST_ACCEPTANCE_WELCOME, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAcceptedProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Celebration message
    await expect(page.getByText('¡Propuesta aceptada!')).toBeVisible();

    // PDF download link
    const pdfLink = page.getByRole('link', { name: /Descargar resumen PDF/i });
    await expect(pdfLink).toBeVisible();
    await expect(pdfLink).toHaveAttribute('href', `/api/proposals/${MOCK_UUID}/pdf/`);
  });

  test('accepted proposal shows onboarding timeline with 3 steps', {
    tag: [...PROPOSAL_POST_ACCEPTANCE_WELCOME, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAcceptedProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    // Onboarding title
    await expect(page.getByText('¿Qué sigue?')).toBeVisible();

    // 3 onboarding steps (use exact match to avoid subtitle collisions)
    await expect(page.getByText('Email de confirmación', { exact: true })).toBeVisible();
    await expect(page.getByText('Llamada de kickoff', { exact: true })).toBeVisible();
    await expect(page.getByText('Setup del proyecto', { exact: true })).toBeVisible();
  });

  test('accepted proposal shows PM WhatsApp contact link', {
    tag: [...PROPOSAL_POST_ACCEPTANCE_WELCOME, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAcceptedProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    const pmLink = page.getByRole('link', { name: /Contactar a tu Project Manager/i });
    await expect(pmLink).toBeVisible();
  });

  test('accepted proposal in English shows English onboarding steps', {
    tag: [...PROPOSAL_POST_ACCEPTANCE_WELCOME, '@role:guest'],
  }, async ({ page }) => {
    const enProposal = { ...mockAcceptedProposal, language: 'en' };

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === `proposals/${MOCK_UUID}/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(enProposal) };
      }
      return null;
    });

    await openClosingPanel(page);

    await expect(page.getByText('Proposal accepted!')).toBeVisible();
    await expect(page.getByText("What's next?")).toBeVisible();
    await expect(page.getByText('Confirmation email', { exact: true })).toBeVisible();
    await expect(page.getByText('Kickoff call', { exact: true })).toBeVisible();
    await expect(page.getByText('Project setup', { exact: true })).toBeVisible();
  });
});
