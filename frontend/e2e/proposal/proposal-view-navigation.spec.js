/**
 * E2E tests for proposal section navigation.
 *
 * Covers: ProposalIndex open/close, clicking an index item to navigate,
 * ProposalIndex hidden when nav-side--left should be visible,
 * keyboard-style prev/next cycling through all sections.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_VIEW } from '../helpers/flow-tags.js';

const MOCK_UUID = 'cccccccc-cccc-cccc-cccc-cccccccccccc';

const mockProposalMultiSection = {
  id: 5,
  uuid: MOCK_UUID,
  title: 'Multi Section Navigation Test',
  client_name: 'Nav Client',
  status: 'sent',
  language: 'es',
  total_investment: '8000000',
  currency: 'COP',
  sections: [
    {
      id: 51,
      section_type: 'greeting',
      title: '👋 Bienvenido',
      order: 0,
      is_enabled: true,
      content_json: { clientName: 'Nav Client', inspirationalQuote: 'Move fast.' },
    },
    {
      id: 52,
      section_type: 'executive_summary',
      title: '🧾 Resumen Ejecutivo',
      order: 1,
      is_enabled: true,
      content_json: {
        index: '1',
        title: 'Resumen ejecutivo',
        paragraphs: ['Solución a medida.'],
        highlightsTitle: 'Incluye',
        highlights: ['Diseño UX'],
      },
    },
    {
      id: 53,
      section_type: 'context_diagnostic',
      title: '🧩 Contexto',
      order: 2,
      is_enabled: true,
      content_json: {
        index: '2',
        title: 'Contexto',
        paragraphs: ['El cliente busca crecer.'],
        issuesTitle: 'Desafíos',
        issues: ['Poca visibilidad'],
        opportunityTitle: 'Oportunidad',
        opportunity: 'Digitalización.',
      },
    },
  ],
  requirement_groups: [],
};

function buildMockHandler() {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposalMultiSection) };
    }
    return null;
  };
}

test.describe('Proposal View Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('ProposalIndex toggle button is visible on load', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // The hamburger toggle button for ProposalIndex should always be visible
    await expect(page.getByTestId('index-toggle')).toBeVisible();
  });

  test('clicking ProposalIndex toggle opens the index panel', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Index panel is hidden initially (translate-x-[-120%])
    const indexPanel = page.getByTestId('index-panel');
    await expect(indexPanel).toHaveAttribute('class', /pointer-events-none/);

    // Click toggle to open
    await page.getByTestId('index-toggle').click();

    // Index panel becomes visible
    await expect(indexPanel).toHaveAttribute('class', /pointer-events-auto/, { timeout: 3000 });
  });

  test('clicking an index item navigates to that section', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Open the index
    await page.getByTestId('index-toggle').click();
    const indexPanel = page.getByTestId('index-panel');
    await expect(indexPanel).toHaveAttribute('class', /pointer-events-auto/, { timeout: 3000 });

    // Click the 3rd item (Contexto) — index item 3
    const thirdItem = indexPanel.getByRole('button').nth(2);
    await thirdItem.click();

    // Index should close after navigation
    await expect(indexPanel).toHaveAttribute('class', /pointer-events-none/, { timeout: 3000 });

    // Previous button should be visible (no longer at first panel)
    await expect(page.getByTestId('nav-prev')).toBeVisible();
  });

  test('ProposalIndex left nav button is hidden when index is open', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // First navigate to section 2 so prev button would normally show
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();

    // Prev button should be visible at section 2
    await expect(page.getByTestId('nav-prev')).toBeVisible({ timeout: 3000 });

    // Open index panel
    await page.getByTestId('index-toggle').click();
    await expect(page.getByTestId('index-panel')).toHaveAttribute('class', /pointer-events-auto/, { timeout: 3000 });

    // The nav-prev button should be hidden when index is open (hideLeft prop)
    await expect(page.getByTestId('nav-prev')).not.toBeVisible();
  });

  test('cycling through all sections reaches the closing panel', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate through all sections
    const nextBtn = page.getByTestId('nav-next');
    let safetyLimit = 15;
    while (await nextBtn.isVisible({ timeout: 500 }).catch(() => false) && safetyLimit-- > 0) {
      await nextBtn.click();
      await expect(page.locator('body')).toBeVisible(); // yield
    }

    // On last panel (proposal_closing), next button is gone
    await expect(page.getByTestId('nav-next')).not.toBeVisible();

    // And accept/reject buttons should be visible (closing panel)
    await expect(page.getByRole('button', { name: /Acepto la propuesta/i })).toBeVisible();
  });
});
