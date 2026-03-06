/**
 * E2E tests for client-facing proposal rendering when sections use paste mode.
 *
 * Covers: RawContentSection rendering for paste-mode sections,
 * markdown rendering in pasted content, structured rendering for form-mode sections,
 * and mixed form/paste mode across sections.
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
      // Section 0: greeting (form mode — no paste)
      _buildSection(901, 'greeting', 'Bienvenido', 0, {
        clientName: 'Test Client',
        inspirationalQuote: 'Think different.',
        _editMode: 'form',
      }),
      // Section 1: executive_summary in PASTE mode with markdown content
      _buildSection(902, 'executive_summary', '🧾 Resumen ejecutivo', 1, {
        index: '1',
        title: 'Resumen ejecutivo',
        paragraphs: ['Old paragraph.'],
        highlightsTitle: 'Incluye',
        highlights: ['Old highlight'],
        _editMode: 'paste',
        rawText: '## Resumen del Proyecto\n\nEste es el resumen **ejecutivo** del proyecto.\n\n- Punto importante 1\n- Punto importante 2\n\n> Una cita relevante sobre el proyecto.',
      }),
      // Section 2: context_diagnostic in FORM mode (structured)
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
      // Section 3: conversion_strategy in PASTE mode
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
      // Section 4: functional_requirements with mixed group modes
      _buildSection(905, 'functional_requirements', '🧩 Requerimientos', 4, {
        index: '7',
        title: 'Requerimientos Funcionales',
        intro: 'Detalle de los requerimientos.',
        groups: [
          {
            id: 'views',
            icon: '🖥️',
            title: 'Vistas',
            description: 'Pantallas del sitio.',
            items: [
              { icon: '🏠', name: 'Home', description: 'Landing.' },
            ],
            _editMode: 'form',
          },
          {
            id: 'components',
            icon: '🧩',
            title: 'Componentes',
            description: '',
            items: [],
            _editMode: 'paste',
            rawText: '### Componentes UI\n\n- **Header**: Navegación principal\n- **Footer**: Links y redes sociales\n- **Card**: Componente reutilizable',
          },
        ],
        additionalModules: [],
      }),
      // Section 5: timeline in FORM mode
      _buildSection(906, 'timeline', '⏳ Cronograma', 5, {
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
  return async ({ _route, apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(proposal),
      };
    }
    // Record view count
    if (apiPath === `proposals/${MOCK_UUID}/record-view/`) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    return null;
  };
}

test.describe('Proposal View — Paste Mode Rendering', () => {
  test('paste-mode section renders RawContentSection with markdown', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for preloader to finish and content to appear
    await page.getByTestId('raw-content').first().waitFor({ state: 'visible', timeout: 10000 });

    // The paste-mode executive_summary should render as RawContentSection
    const rawContentSections = page.getByTestId('raw-content');
    const count = await rawContentSections.count();
    // Should have at least 2 raw content sections (exec_summary + conversion_strategy paste modes)
    // Plus 1 for the components group paste mode
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('paste-mode section renders markdown headings and bold text', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for content to appear
    const rawContentCard = page.getByTestId('raw-content-card').first();
    await rawContentCard.waitFor({ state: 'visible', timeout: 10000 });
    await expect(rawContentCard).toBeVisible();

    // The markdown "## Resumen del Proyecto" should become an h2
    const heading = rawContentCard.locator('h2');
    await expect(heading).toBeVisible();

    // Bold text "**ejecutivo**" should render as <strong>
    const boldText = rawContentCard.locator('strong');
    const boldCount = await boldText.count();
    expect(boldCount).toBeGreaterThanOrEqual(1);
  });

  test('paste-mode section shows content in a styled card with rounded borders', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for content to appear
    const rawContentCard = page.getByTestId('raw-content-card').first();
    await rawContentCard.waitFor({ state: 'visible', timeout: 10000 });
    await expect(rawContentCard).toBeVisible();

    // Verify the card has rounded corners (rounded-2xl class)
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

    // Wait for structured content to appear
    const contextPanel = page.locator('[data-section-type="context_diagnostic"]');
    await contextPanel.waitFor({ state: 'visible', timeout: 10000 });
    await expect(contextPanel).toBeVisible();

    // Should NOT have raw-content inside it
    const rawInContext = contextPanel.getByTestId('raw-content');
    expect(await rawInContext.count()).toBe(0);
  });

  test('paste-mode section displays the section title', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for content to appear
    const rawContentSection = page.getByTestId('raw-content').first();
    await rawContentSection.waitFor({ state: 'visible', timeout: 10000 });
    const title = rawContentSection.locator('h2');
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

    // Wait for the index "1" (from executive_summary paste section) to appear
    const rawContentIndex = page.getByTestId('raw-content-index').getByText('1');
    await rawContentIndex.waitFor({ state: 'visible', timeout: 10000 });
    await expect(rawContentIndex).toBeVisible();
  });

  test('functional_requirements group in paste mode renders as RawContentSection', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for functional requirements groups to appear
    const groupPanel = page.locator('[data-section-type="functional_requirements_group"]');
    await expect(groupPanel).toHaveCount(2, { timeout: 10000 });

    // At least one group panel should contain raw-content (the paste-mode "Componentes" group)
    const pasteGroupContent = groupPanel.filter({ has: page.getByTestId('raw-content') });
    await expect(pasteGroupContent).toHaveCount(1);
  });

  test('mixed form/paste proposal: form sections use structured components', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for greeting to appear
    const greetingPanel = page.locator('[data-section-type="greeting"]');
    await greetingPanel.waitFor({ state: 'visible', timeout: 10000 });

    // greeting (form) should NOT have raw-content
    expect(await greetingPanel.getByTestId('raw-content').count()).toBe(0);

    // timeline (form) should NOT have raw-content
    const timelinePanel = page.locator('[data-section-type="timeline"]');
    expect(await timelinePanel.getByTestId('raw-content').count()).toBe(0);
  });

  test('markdown list items render correctly in paste section', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    const proposal = buildMockProposal();
    await mockApi(page, buildMockHandler(proposal));
    await page.goto(`/proposal/${MOCK_UUID}`);
    await page.waitForLoadState('networkidle');

    // Wait for content to appear
    const rawContentCard = page.getByTestId('raw-content-card').first();
    await rawContentCard.waitFor({ state: 'visible', timeout: 10000 });
    const listItems = rawContentCard.locator('li');
    const liCount = await listItems.count();
    expect(liCount).toBeGreaterThanOrEqual(2);
  });

  test('all-form proposal renders zero RawContentSection components', {
    tag: [...PROPOSAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    // Create a proposal with all sections in form mode
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

    // Wait for page to load, then check no raw-content sections exist
    await page.locator('[data-section-type="greeting"]').waitFor({ state: 'visible', timeout: 10000 });
    const rawContentSections = page.getByTestId('raw-content');
    expect(await rawContentSections.count()).toBe(0);
  });
});
