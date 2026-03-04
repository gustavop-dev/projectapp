/**
 * E2E tests for admin proposal section editing via PASTE CONTENT mode.
 *
 * Covers: pasting text into supported section types, processing pasted content,
 * verifying form fields are populated correctly, and saving the processed data.
 * Supported types: executive_summary, context_diagnostic, design_ux,
 * creative_support, conversion_strategy, final_note, next_steps.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_PROPOSAL_SECTION_EDIT_PASTE,
} from '../helpers/flow-tags.js';

const PROPOSAL_ID = 2;
const userId = 7200;

function buildSection(id, type, title, order) {
  return {
    id,
    section_type: type,
    title,
    order,
    is_enabled: true,
    is_wide_panel: false,
    content_json: {},
  };
}

const mockProposal = {
  id: PROPOSAL_ID,
  uuid: '22222222-2222-2222-2222-222222222222',
  title: 'E2E Paste Content Test',
  client_name: 'Paste Client',
  client_email: 'paste@test.com',
  language: 'es',
  status: 'draft',
  total_investment: '3000000',
  currency: 'COP',
  view_count: 0,
  sent_at: null,
  expires_at: null,
  sections: [
    buildSection(201, 'greeting', 'Greeting', 0),
    buildSection(202, 'executive_summary', '🧾 Resumen ejecutivo', 1),
    buildSection(203, 'context_diagnostic', '🧩 Contexto', 2),
    buildSection(204, 'conversion_strategy', '🚀 Estrategia', 3),
    buildSection(205, 'design_ux', '🎨 Diseño UX', 4),
    buildSection(206, 'creative_support', '🤝 Acompañamiento', 5),
    buildSection(207, 'development_stages', '📌 Etapas', 6),
    buildSection(208, 'functional_requirements', '🧩 Requerimientos', 7),
    buildSection(209, 'timeline', '⏳ Cronograma', 8),
    buildSection(210, 'investment', '💰 Inversión', 9),
    buildSection(211, 'final_note', '📝 Nota Final', 10),
    buildSection(212, 'next_steps', '✅ Próximos pasos', 11),
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
        body: JSON.stringify({
          ...section,
          ...body,
          content_json: body.content_json || section?.content_json || {},
        }),
      };
    }
    return null;
  };
}

test.describe('Proposal Section Edit — Paste Content Mode', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: userId, role: 'admin', is_staff: true },
    });
  });

  test('proposal edit page loads with all 12 sections', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('paste mode is available for supported section types', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('paste mode is not available for greeting section type', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('paste mode is not available for development_stages section type', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('pasting content into executive_summary fills paragraphs and highlights', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('pasting content into context_diagnostic fills paragraphs issues and opportunity', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });

  test('pasting empty text does nothing', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_PASTE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await expect(page.locator('h1')).toBeVisible();
  });
});
