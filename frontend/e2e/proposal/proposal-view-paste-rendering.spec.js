/**
 * E2E tests for client-facing proposal rendering when sections use paste mode.
 *
 * Covers: RawContentSection rendering for paste-mode sections,
 * markdown rendering in pasted content, structured rendering for form-mode sections,
 * and mixed form/paste mode across sections.
 *
 * NOTE: The proposal view is panel-based (one section visible at a time).
 * Tests must navigate to the correct panel before asserting content.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_VIEW } from '../helpers/flow-tags.js';

const MOCK_UUID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';

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

/**
 * Build a mock proposal with sections in various form/paste modes.
 * Panel order: greeting(0) → exec_summary/paste(1) → context/form(2)
 *   → conversion/paste(3) → FR(4) → timeline/form(5) → closing(6)
 */
function buildMockProposal() {
  return {
    id: 99,
    uuid: MOCK_UUID,
    title: 'Paste Rendering Test Proposal',
    client_name: 'Test Client',
    client_email: 'client@test.com',
    language: 'es',
    status: 'sent',
    total_investment: '5000000',
    currency: 'COP',
    view_count: 0,
    sent_at: '2026-01-01T00:00:00Z',
    expires_at: null,
    sections: [
      _buildSection(901, 'greeting', 'Bienvenido', 0, {
        clientName: 'Test Client',
        inspirationalQuote: 'Think different.',
        _editMode: 'form',
      }),
      _buildSection(902, 'executive_summary', '🧾 Resumen ejecutivo', 1, {
        index: '1',
        title: 'Resumen ejecutivo',
        paragraphs: ['Old paragraph.'],
        highlightsTitle: 'Incluye',
        highlights: ['Old highlight'],
        _editMode: 'paste',
        rawText: '## Resumen del Proyecto\n\nEste es el resumen **ejecutivo** del proyecto.\n\n- Punto importante 1\n- Punto importante 2\n\n> Una cita relevante sobre el proyecto.',
      }),
      _buildSection(903, 'context_diagnostic', '🧩 Contexto', 2, {
        index: '2',
        title: 'Contexto y Diagnóstico',
        paragraphs: ['El cliente necesita una presencia digital.'],
        issuesTitle: 'Desafíos',
        issues: ['Sin web profesional', 'Difícil captar clientes'],
        opportunityTitle: 'Oportunidad',
        opportunity: 'Crear una plataforma de confianza.',
        _editMode: 'form',
      }),
      _buildSection(904, 'conversion_strategy', '🚀 Estrategia', 3, {
        index: '3',
        title: 'Estrategia de Conversión',
        intro: '',
        steps: [],
        resultTitle: '',
        result: '',
        _editMode: 'paste',
        rawText: '### Estrategia\n\nLa página se construirá como **herramienta de conversión**.\n\n1. Captar atención\n2. Construir confianza\n3. Generar acción',
      }),
      _buildSection(906, 'timeline', '⏳ Cronograma', 4, {
        index: '8',
        title: 'Cronograma',
        introText: 'Fases del proyecto.',
        totalDuration: '1 mes',
        phases: [
          { title: 'Diseño', duration: '1 semana', description: 'Diseño visual.', tasks: ['Wireframes'], milestone: 'Aprobación' },
        ],
        _editMode: 'form',
      }),
    ],
    requirement_groups: [],
  };
}

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
    return null;
  };
}

/**
 * Navigate forward N panels using the nav-next button.
 */
async function navigateToPanel(page, panelIndex) {
  for (let i = 0; i < panelIndex; i++) {
    const nextBtn = page.getByTestId('nav-next');
    await expect(nextBtn).toBeVisible();
    await nextBtn.click();
    await expect(page.locator('body')).toBeVisible();
  }
}

test.describe('Proposal View — Paste Mode Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('paste-mode section renders RawContentSection with markdown', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate from greeting (panel 0) to executive_summary paste (panel 1)
    await navigateToPanel(page, 1);

    // Panel should show RawContentSection for paste-mode exec_summary
    const rawContent = page.getByTestId('raw-content');
    await expect(rawContent).toBeVisible();

    // Verify the panel is the executive_summary type
    const panel = page.locator('[data-section-type="executive_summary"]');
    await expect(panel).toBeVisible();
  });

  test('paste-mode section renders markdown headings and bold text', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to executive_summary paste panel (index 1)
    await navigateToPanel(page, 1);

    const rawContentCard = page.getByTestId('raw-content-card');
    await expect(rawContentCard).toBeVisible();

    // The markdown "## Resumen del Proyecto" should become an h2
    await expect(rawContentCard.locator('h2')).toBeVisible();

    // Bold text "**ejecutivo**" should render as <strong>
    const boldCount = await rawContentCard.locator('strong').count();
    expect(boldCount).toBeGreaterThanOrEqual(1);
  });

  test('paste-mode section shows content in a styled card with rounded borders', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to executive_summary paste panel (index 1)
    await navigateToPanel(page, 1);

    const rawContentCard = page.getByTestId('raw-content-card');
    await expect(rawContentCard).toBeVisible();

    // Verify the card has rounded corners and backdrop-blur
    const classes = await rawContentCard.getAttribute('class');
    expect(classes).toContain('rounded-2xl');
    expect(classes).toContain('backdrop-blur');
  });

  test('form-mode section renders structured component, NOT RawContentSection', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to context_diagnostic form panel (index 2)
    await navigateToPanel(page, 2);

    // Panel should be context_diagnostic
    const panel = page.locator('[data-section-type="context_diagnostic"]');
    await expect(panel).toBeVisible();

    // Form-mode panel should NOT contain RawContentSection
    expect(await panel.getByTestId('raw-content').count()).toBe(0);
  });

  test('paste-mode section displays the section title', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to executive_summary paste panel (index 1)
    await navigateToPanel(page, 1);

    const rawContent = page.getByTestId('raw-content');
    await expect(rawContent).toBeVisible();
    const title = rawContent.getByRole('heading', { level: 2, name: /Resumen ejecutivo/i });
    await expect(title).toBeVisible();
    const titleText = await title.textContent();
    expect(titleText.trim()).toBeTruthy();
  });

  test('paste-mode section displays the section index number', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to executive_summary paste panel (index 1)
    await navigateToPanel(page, 1);

    // The section index "1" should be visible
    const rawContentIndex = page.getByTestId('raw-content-index');
    await expect(rawContentIndex).toBeVisible();
    await expect(rawContentIndex).toContainText('1');
  });

  test('second paste-mode section also renders as RawContentSection', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to conversion_strategy paste panel (index 3)
    await navigateToPanel(page, 3);

    // Panel should be conversion_strategy
    const panel = page.locator('[data-section-type="conversion_strategy"]');
    await expect(panel).toBeVisible();

    // Should render as RawContentSection
    await expect(page.getByTestId('raw-content')).toBeVisible();
    await expect(page.getByTestId('raw-content-card')).toBeVisible();
  });

  test('mixed proposal: greeting (form) has no raw-content, timeline (form) has no raw-content', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Panel 0: greeting (form) — should NOT have raw-content
    const greetingPanel = page.locator('[data-section-type="greeting"]');
    await expect(greetingPanel).toBeVisible();
    expect(await greetingPanel.getByTestId('raw-content').count()).toBe(0);

    // Navigate to timeline (form) panel (index 4)
    await navigateToPanel(page, 4);
    const timelinePanel = page.locator('[data-section-type="timeline"]');
    await expect(timelinePanel).toBeVisible();
    expect(await timelinePanel.getByTestId('raw-content').count()).toBe(0);
  });

  test('markdown list items render correctly in paste section', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Navigate to executive_summary paste panel (index 1)
    await navigateToPanel(page, 1);

    const rawContentCard = page.getByTestId('raw-content-card');
    await expect(rawContentCard).toBeVisible();
    const liCount = await rawContentCard.locator('li').count();
    expect(liCount).toBeGreaterThanOrEqual(2);
  });

  test('all-form proposal renders zero RawContentSection components', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const allFormProposal = {
      id: 100,
      uuid: MOCK_UUID,
      title: 'All Form Proposal',
      client_name: 'Form Client',
      client_email: 'form@test.com',
      language: 'es',
      status: 'sent',
      total_investment: '3000000',
      currency: 'COP',
      view_count: 0,
      sent_at: '2026-01-01T00:00:00Z',
      expires_at: null,
      sections: [
        _buildSection(801, 'greeting', 'Greeting', 0, {
          clientName: 'Form Client', inspirationalQuote: 'Quote.', _editMode: 'form',
        }),
        _buildSection(802, 'executive_summary', 'Summary', 1, {
          index: '1', title: 'Summary', paragraphs: ['P1'], highlightsTitle: 'H', highlights: ['H1'], _editMode: 'form',
        }),
      ],
      requirement_groups: [],
    };

    await mockApi(page, buildMockHandler(allFormProposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Panel 0: greeting (form) — no raw-content
    const greetingPanel = page.locator('[data-section-type="greeting"]');
    await expect(greetingPanel).toBeVisible();
    expect(await greetingPanel.getByTestId('raw-content').count()).toBe(0);

    // Navigate to panel 1: executive_summary (form) — no raw-content
    await navigateToPanel(page, 1);
    const summaryPanel = page.locator('[data-section-type="executive_summary"]');
    await expect(summaryPanel).toBeVisible();
    expect(await summaryPanel.getByTestId('raw-content').count()).toBe(0);
  });
});
