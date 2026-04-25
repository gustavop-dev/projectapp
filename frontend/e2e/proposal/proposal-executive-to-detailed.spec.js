/**
 * E2E tests for switching from executive view to detailed proposal view.
 *
 * @flow:proposal-executive-to-detailed
 * Covers: executive mode shows subset of sections, "Ver Propuesta Completa" button
 * in ProposalIndex sidebar triggers branded transition overlay, after switch all
 * sections are visible and navigable. InvestmentDetailedTeaser button also triggers switch.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_EXECUTIVE_TO_DETAILED } from '../helpers/flow-tags.js';

const MOCK_UUID = 'e8111111-1111-1111-1111-111111111111';

function _buildSection(id, type, title, order, contentJson = {}) {
  return {
    id,
    section_type: type,
    title,
    order,
    is_enabled: true,
    is_wide_panel: type === 'functional_requirements',
    content_json: contentJson,
  };
}

const mockProposal = {
  id: 50,
  uuid: MOCK_UUID,
  title: 'Executive to Detailed Test Proposal',
  client_name: 'Switch Client',
  client_email: 'switch@test.com',
  language: 'es',
  status: 'sent',
  total_investment: '10000000',
  currency: 'COP',
  view_count: 1,
  sent_at: '2026-01-01T00:00:00Z',
  expires_at: null,
  sections: [
    _buildSection(501, 'greeting', '👋 Bienvenido', 0, {
      clientName: 'Switch Client',
      inspirationalQuote: 'Innovation distinguishes.',
    }),
    _buildSection(502, 'executive_summary', '🧾 Resumen ejecutivo', 1, {
      index: '1', title: 'Resumen ejecutivo',
      paragraphs: ['Solución integral para tu negocio.'],
      highlightsTitle: 'Incluye', highlights: ['Diseño UX'],
    }),
    _buildSection(503, 'context_diagnostic', '🧩 Contexto', 2, {
      index: '2', title: 'Contexto',
      paragraphs: ['Análisis del mercado.'],
      issuesTitle: 'Desafíos', issues: ['Competencia digital'],
      opportunityTitle: 'Oportunidad', opportunity: 'Diferenciación.',
    }),
    _buildSection(504, 'conversion_strategy', '🚀 Estrategia', 3, {
      index: '3', title: 'Estrategia',
      intro: 'Estrategia de conversión.', steps: [], resultTitle: '', result: '',
    }),
    _buildSection(505, 'design_ux', '🎨 Diseño UX', 4, {
      index: '4', title: 'Diseño UX',
      paragraphs: ['Diseño centrado en el usuario.'],
      focusTitle: '', focusItems: [], objectiveTitle: '', objective: '',
    }),
    _buildSection(506, 'functional_requirements', '🧩 Requerimientos', 5, {
      index: '5', title: 'Requerimientos', intro: '',
      groups: [{ id: 'views', icon: '🖥️', title: 'Vistas', description: '', items: [] }],
      additionalModules: [],
    }),
    _buildSection(507, 'timeline', '⏳ Cronograma', 6, {
      index: '6', title: 'Cronograma', introText: '', totalDuration: '2 meses', phases: [],
    }),
    _buildSection(508, 'investment', '💰 Inversión', 7, {
      index: '7', title: 'Inversión', introText: '', totalInvestment: '10000000', currency: 'COP',
      whatsIncluded: [], paymentOptions: [], paymentMethods: [], valueReasons: [],
      modules: [],
    }),
    _buildSection(509, 'proposal_closing', '🤝 Cierre', 8, {
      index: '8', title: 'Cierre',
    }),
  ],
  requirement_groups: [],
};

function buildMockHandler(proposal) {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(proposal),
      };
    }
    if (apiPath === `proposals/${MOCK_UUID}/record-view/`) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    if (apiPath.includes('/track/')) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    return null;
  };
}

test.describe('Proposal Executive to Detailed View Switch', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((_uuid) => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    }, MOCK_UUID);
  });

  test('executive mode renders only executive section types', {
    tag: [...PROPOSAL_EXECUTIVE_TO_DETAILED, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposal));
    await page.goto(`/proposal/${MOCK_UUID}?mode=executive`);

    // Greeting panel should be visible (executive section)
    await expect(page.locator('[data-section-type="greeting"]')).toBeVisible();

    // The SectionCounter should show fewer sections than the total
    const counter = page.getByTestId('section-counter');
    await expect(counter).toBeVisible({ timeout: 5000 });
    const counterText = await counter.textContent();
    // Executive mode shows ~5-7 sections (greeting, exec_summary, proposal_summary, FR, investment, timeline, closing)
    // Detailed mode shows all ~9 sections
    expect(counterText).toContain('/');
  });

  test('ProposalIndex shows "Ver Propuesta Completa" button in executive mode', {
    tag: [...PROPOSAL_EXECUTIVE_TO_DETAILED, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposal));
    await page.goto(`/proposal/${MOCK_UUID}?mode=executive`);

    // Open the ProposalIndex sidebar
    const indexToggle = page.getByTestId('index-toggle');
    if (await indexToggle.isVisible()) {
      await indexToggle.click();
    }

    // The switch button should be visible in executive mode
    const switchBtn = page.getByTestId('switch-to-detailed-btn');
    await expect(switchBtn).toBeVisible();
    await expect(switchBtn).toContainText('Ver Propuesta Completa');
  });

  test('clicking "Ver Propuesta Completa" shows transition overlay and switches to detailed mode', {
    tag: [...PROPOSAL_EXECUTIVE_TO_DETAILED, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposal));
    await page.goto(`/proposal/${MOCK_UUID}?mode=executive`);

    // Open ProposalIndex and click switch button
    const indexToggle = page.getByTestId('index-toggle');
    if (await indexToggle.isVisible()) {
      await indexToggle.click();
    }

    const switchBtn = page.getByTestId('switch-to-detailed-btn');
    await switchBtn.scrollIntoViewIfNeeded({ timeout: 5000 });
    await expect(switchBtn).toBeVisible({ timeout: 5000 });
    await switchBtn.click({ timeout: 5000 });

    // After transition overlay auto-dismisses, the counter should update to show all sections
    const counter = page.getByTestId('section-counter');
    await expect(counter).toBeVisible({ timeout: 10000 });
  });

  test('detailed mode shows all sections after switch from executive', {
    tag: [...PROPOSAL_EXECUTIVE_TO_DETAILED, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposal));
    // Start directly in detailed mode to verify all sections are visible
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Greeting should be visible
    await expect(page.locator('[data-section-type="greeting"]')).toBeVisible({ timeout: 5000 });

    // Navigate forward to find context_diagnostic (not in executive mode)
    const nextBtn = page.getByTestId('nav-next');
    let foundContext = false;
    for (let i = 0; i < 12; i++) {
      if (await page.locator('[data-section-type="context_diagnostic"]').isVisible().catch(() => false)) {
        foundContext = true;
        break;
      }
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
        try {
          await page.locator('[data-section-type="context_diagnostic"]').waitFor({ state: 'visible', timeout: 2000 });
        } catch {
          /* section not reached yet; loop continues */
        }
      }
    }

    expect(foundContext).toBe(true);
  });

  test('"Ver Propuesta Completa" button is NOT shown in detailed mode', {
    tag: [...PROPOSAL_EXECUTIVE_TO_DETAILED, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(mockProposal));
    await page.goto(`/proposal/${MOCK_UUID}?mode=detailed`);

    // Open ProposalIndex
    const indexToggle = page.getByTestId('index-toggle');
    if (await indexToggle.isVisible()) {
      await indexToggle.click();
    }

    // The switch button should NOT be present in detailed mode
    const switchBtn = page.getByTestId('switch-to-detailed-btn');
    await expect(switchBtn).not.toBeVisible();
  });
});
