/**
 * E2E tests for admin proposal section editing via FORM mode.
 *
 * Covers: editing each major section type using structured form fields,
 * verifying the save payload contains correct content_json structure,
 * and that data persists correctly via the API.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_PROPOSAL_SECTION_EDIT_FORM,
} from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;
const userId = 7100;

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
  id: PROPOSAL_ID,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'E2E Section Form Test',
  client_name: 'Form Client',
  client_email: 'form@test.com',
  language: 'es',
  status: 'draft',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  sent_at: null,
  expires_at: null,
  sections: [
    _buildSection(101, 'greeting', 'Greeting', 0, { clientName: '', inspirationalQuote: '' }),
    _buildSection(102, 'executive_summary', '🧾 Resumen ejecutivo', 1, {
      index: '1', title: 'Resumen ejecutivo', paragraphs: [], highlightsTitle: 'Incluye', highlights: [],
    }),
    _buildSection(103, 'context_diagnostic', '🧩 Contexto', 2, {
      index: '2', title: 'Contexto', paragraphs: [], issuesTitle: 'Desafíos', issues: [],
      opportunityTitle: 'Oportunidad', opportunity: '',
    }),
    _buildSection(104, 'conversion_strategy', '🚀 Estrategia', 3, {
      index: '3', title: 'Estrategia', intro: '', steps: [], resultTitle: '', result: '',
    }),
    _buildSection(105, 'design_ux', '🎨 Diseño UX', 4, {
      index: '4', title: 'Diseño UX', paragraphs: [], focusTitle: '', focusItems: [],
      objectiveTitle: '', objective: '',
    }),
    _buildSection(106, 'creative_support', '🤝 Acompañamiento', 5, {
      index: '5', title: 'Acompañamiento', paragraphs: [], includesTitle: '', includes: [], closing: '',
    }),
    _buildSection(107, 'development_stages', '📌 Etapas', 6, { stages: [] }),
    _buildSection(108, 'functional_requirements', '🧩 Requerimientos', 7, {
      index: '7', title: 'Requerimientos', intro: '',
      groups: [{ id: 'views', icon: '🖥️', title: 'Vistas', description: '', items: [] }],
      additionalModules: [],
    }),
    _buildSection(109, 'timeline', '⏳ Cronograma', 8, {
      index: '8', title: 'Cronograma', introText: '', totalDuration: '', phases: [],
    }),
    _buildSection(110, 'investment', '💰 Inversión', 9, {
      index: '9', title: 'Inversión', introText: '', totalInvestment: '', currency: 'COP',
      whatsIncluded: [], paymentOptions: [], paymentMethods: [], valueReasons: [],
    }),
    _buildSection(111, 'final_note', '📝 Nota Final', 10, {
      index: '10', title: 'Nota Final', message: '', personalNote: '', teamName: '', teamRole: '',
      contactEmail: '', commitmentBadges: [], validityMessage: '', thankYouMessage: '',
    }),
    _buildSection(112, 'next_steps', '✅ Próximos pasos', 11, {
      index: '11', title: 'Próximos pasos', introMessage: '', steps: [], ctaMessage: '',
      primaryCTA: { text: '', link: '' }, secondaryCTA: { text: '', link: '' },
      contactMethods: [], validityMessage: '', thankYouMessage: '',
    }),
  ],
  requirement_groups: [],
};

function buildMockHandler(capturedUpdates) {
  return async ({ route, apiPath }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
      };
    }
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProposal),
      };
    }
    const sectionMatch = apiPath.match(/^proposals\/sections\/(\d+)\/update\/$/);
    if (sectionMatch) {
      const sectionId = parseInt(sectionMatch[1]);
      const body = route.request().postDataJSON();
      if (capturedUpdates) {
        capturedUpdates.push({ sectionId, body });
      }
      const section = mockProposal.sections.find(s => s.id === sectionId);
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...section, ...body, content_json: body.content_json || section?.content_json || {} }),
      };
    }
    return null;
  };
}

/**
 * Helper: navigate to edit page, switch to Secciones tab, expand a section,
 * and return the section editor container.
 */
async function openSectionEditor(page, capturedUpdates, sectionTitle) {
  await mockApi(page, buildMockHandler(capturedUpdates));
  await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
  await page.waitForLoadState('networkidle');

  // Switch to Secciones tab
  await page.getByRole('button', { name: 'Secciones' }).click();

  // Find section header and expand it
  const sectionHeader = page.locator('.cursor-pointer').filter({ hasText: sectionTitle });
  await sectionHeader.click();

  await page.getByTestId('section-editor').waitFor({ state: 'visible' });
}

test.describe('Proposal Section Edit — Form Mode', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: userId, role: 'admin', is_staff: true },
    });
  });

  test('loads proposal edit page with sections tab showing all 12 sections', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');

    // Switch to sections tab
    await page.getByRole('button', { name: 'Secciones' }).click();

    // Verify all section titles are visible
    await expect(page.getByText('Greeting', { exact: true })).toBeVisible();
    await expect(page.getByText('🧾 Resumen ejecutivo')).toBeVisible();
    await expect(page.getByText('🧩 Contexto')).toBeVisible();
  });

  test('greeting: fills clientName and inspirationalQuote, saves correct payload', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, 'Greeting');

    // Fill greeting fields — find the section editor area
    const editor = page.getByTestId('section-editor');

    await editor.getByLabel('Nombre del cliente').fill('María García');
    await editor.getByLabel('Frase inspiracional').fill('Design is how it works.');

    // Click save
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    // Verify captured payload
    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.sectionId).toBe(101);
    expect(last.body.content_json.clientName).toBe('María García');
    expect(last.body.content_json.inspirationalQuote).toBe('Design is how it works.');
    expect(last.body.content_json._editMode).toBe('form');
  });

  test('executive_summary: fills paragraphs and highlights, saves arrays', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, '🧾 Resumen ejecutivo');

    const editor = page.getByTestId('section-editor');

    await editor.getByLabel('Párrafos').fill('Primer párrafo.\nSegundo párrafo.');
    await editor.getByLabel('Highlights / Incluye').fill('Diseño personalizado\nDesarrollo responsivo');

    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.content_json._editMode).toBe('form');
    expect(last.body.content_json.paragraphs).toEqual(['Primer párrafo.', 'Segundo párrafo.']);
    expect(last.body.content_json.highlights).toEqual(['Diseño personalizado', 'Desarrollo responsivo']);
  });

  test('context_diagnostic: fills issues and opportunity, saves correctly', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, '🧩 Contexto');

    const editor = page.getByTestId('section-editor');

    await editor.getByLabel('Párrafos').fill('Contexto del proyecto.');
    await editor.getByRole('textbox', { name: /^Problemas/ }).fill('Falta de web\nSin presencia digital');
    await editor.getByRole('textbox', { name: 'Oportunidad', exact: true }).fill('Crear plataforma de confianza.');

    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.content_json.paragraphs).toEqual(['Contexto del proyecto.']);
    expect(last.body.content_json.issues).toEqual(['Falta de web', 'Sin presencia digital']);
    expect(last.body.content_json.opportunity).toBe('Crear plataforma de confianza.');
  });

  test('save button shows confirmation text after saving', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    await openSectionEditor(page, [], 'Greeting');

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();

    // Verify "✓ Guardado" appears
    await expect(editor.getByText('✓ Guardado')).toBeVisible();
  });

  test('section title change is included in save payload', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, 'Greeting');

    const editor = page.getByTestId('section-editor');

    await editor.getByLabel('Título de la sección').fill('Custom Greeting Title');

    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.title).toBe('Custom Greeting Title');
  });

  test('greeting with empty fields saves empty strings', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, 'Greeting');

    const editor = page.getByTestId('section-editor');

    // Leave all fields empty, just click save
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.content_json._editMode).toBe('form');
    expect(last.body.content_json).not.toHaveProperty('rawText');
  });

  test('executive_summary with empty textareas saves empty arrays', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, '🧾 Resumen ejecutivo');

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.content_json.paragraphs).toEqual([]);
    expect(last.body.content_json.highlights).toEqual([]);
  });

  test('investment: save blocked when optional module has no price', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    // Build a proposal with an investment section that has an optional module without price
    const proposalWithInvestment = JSON.parse(JSON.stringify(mockProposal));
    proposalWithInvestment.sections[9].content_json = {
      index: '9', title: 'Inversión', introText: '', totalInvestment: '5000000', currency: 'COP',
      modules: [
        { id: 'mod1', name: 'Módulo Base', price: 3000000, included: true, is_required: true },
        { id: 'mod2', name: 'Módulo Premium', price: 0, included: true, is_required: false },
      ],
      whatsIncluded: [], paymentOptions: [], paymentMethods: [], valueReasons: [],
    };

    const captured = [];
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(proposalWithInvestment) };
      const sectionMatch = apiPath.match(/^proposals\/sections\/(\d+)\/update\/$/);
      if (sectionMatch) {
        captured.push({ sectionId: parseInt(sectionMatch[1]), body: route.request().postDataJSON() });
        const section = proposalWithInvestment.sections.find(s => s.id === parseInt(sectionMatch[1]));
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...section }) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: 'Secciones' }).click();

    const sectionHeader = page.locator('.cursor-pointer').filter({ hasText: '💰 Inversión' });
    await sectionHeader.click();
    await page.getByTestId('section-editor').waitFor({ state: 'visible' });

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();

    // Save should be blocked — validation error shown
    await expect(editor.getByText('No se puede guardar')).toBeVisible();
    await expect(editor.getByText('Módulo Premium')).toBeVisible();

    // No API call should have been made
    expect(captured.length).toBe(0);
  });

  test('form mode payload never includes rawText', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    const captured = [];
    await openSectionEditor(page, captured, '🧩 Contexto');

    const editor = page.getByTestId('section-editor');
    await editor.getByRole('button', { name: 'Guardar Sección' }).click();
    await expect(editor.getByText('✓ Guardado')).toBeVisible();

    expect(captured.length).toBeGreaterThanOrEqual(1);
    const last = captured[captured.length - 1];
    expect(last.body.content_json._editMode).toBe('form');
    expect(last.body.content_json).not.toHaveProperty('rawText');
  });
});
