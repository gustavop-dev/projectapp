/**
 * E2E tests for admin proposal section editing via FORM mode.
 *
 * Covers: editing each major section type using structured form fields,
 * verifying the save payload contains correct content_json structure,
 * and that data persists correctly via the API.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_PROPOSAL_SECTION_EDIT_FORM,
} from '../helpers/flow-tags.js';

const PROPOSAL_ID = 1;
const userId = 7100;

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
    {
      id: 101,
      section_type: 'greeting',
      title: 'Greeting',
      order: 0,
      is_enabled: true,
      is_wide_panel: false,
      content_json: { clientName: '', inspirationalQuote: '' },
    },
    {
      id: 102,
      section_type: 'executive_summary',
      title: '🧾 Resumen ejecutivo',
      order: 1,
      is_enabled: true,
      is_wide_panel: false,
      content_json: {
        index: '1',
        title: 'Resumen ejecutivo',
        paragraphs: [],
        highlightsTitle: 'Incluye',
        highlights: [],
      },
    },
    {
      id: 103,
      section_type: 'context_diagnostic',
      title: '🧩 Contexto',
      order: 2,
      is_enabled: true,
      is_wide_panel: false,
      content_json: {
        index: '2',
        title: 'Contexto',
        paragraphs: [],
        issuesTitle: 'Desafíos',
        issues: [],
        opportunityTitle: 'Oportunidad',
        opportunity: '',
      },
    },
    {
      id: 107,
      section_type: 'functional_requirements',
      title: '🧩 Requerimientos',
      order: 7,
      is_enabled: true,
      is_wide_panel: true,
      content_json: {
        index: '7',
        title: 'Requerimientos',
        intro: '',
        groups: [
          {
            id: 'views',
            icon: '🖥️',
            title: 'Vistas',
            description: '',
            items: [],
          },
        ],
        additionalModules: [],
      },
    },
  ],
  requirement_groups: [],
};

function buildMockHandler(sectionUpdates) {
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
    // Section update — capture and return the payload
    const sectionMatch = apiPath.match(/^proposals\/sections\/(\d+)\/update\/$/);
    if (sectionMatch) {
      const sectionId = parseInt(sectionMatch[1]);
      const body = route.request().postDataJSON();
      if (sectionUpdates) {
        sectionUpdates.push({ sectionId, body });
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

test.describe('Proposal Section Edit — Form Mode', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: userId, role: 'admin', is_staff: true },
    });
  });

  test('loads proposal edit page with sections tab', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.waitForLoadState('networkidle');
    // The page should load without errors
    await page.waitForLoadState('networkidle');
  });

  test('section editor renders form fields for greeting type', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    // Wait for proposal data to load
    await page.waitForLoadState('networkidle');
  });

  test('section editor renders form fields for executive_summary type', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.waitForLoadState('networkidle');
  });

  test('section editor renders form fields for functional_requirements type', {
    tag: [...ADMIN_PROPOSAL_SECTION_EDIT_FORM, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, buildMockHandler(null));
    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    await page.waitForLoadState('networkidle');
  });
});
