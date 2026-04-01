/**
 * Public proposal technical view mode (?mode=technical).
 *
 * @flow:proposal-technical-view
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PROPOSAL_TECHNICAL_VIEW } from '../helpers/flow-tags.js';

const MOCK_UUID = 'tech-view-1111-2222-3333-444444444444';

const mockProposal = {
  id: 901,
  uuid: MOCK_UUID,
  title: 'Technical View Test',
  client_name: 'Tech Client',
  client_email: 'tech@test.com',
  language: 'es',
  status: 'sent',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  sent_at: '2026-01-01T00:00:00Z',
  expires_at: null,
  selected_modules: [],
  sections: [
    {
      id: 9101,
      section_type: 'technical_document',
      title: 'Documento técnico',
      order: 0,
      is_enabled: true,
      is_wide_panel: true,
      content_json: {
        purpose: 'E2E propósito documento técnico',
        stack: [{ layer: 'App', technology: 'Vue', rationale: 'SPA' }],
        epics: [
          {
            epicKey: 'e2e-epic',
            title: 'Épica E2E',
            requirements: [
              { title: 'Req siempre visible', description: 'E2E base scope' },
              {
                title: 'Req módulo oculto',
                description: 'E2E linked hidden when module not selected',
                linked_module_ids: ['module-hidden-e2e'],
              },
            ],
          },
        ],
      },
    },
    {
      id: 9102,
      section_type: 'final_note',
      title: 'Nota final',
      order: 1,
      is_enabled: true,
      is_wide_panel: false,
      content_json: {
        validityMessage: 'Validez',
        thankYouMessage: 'Gracias',
      },
    },
  ],
  requirement_groups: [],
};

function buildMockHandler() {
  return async ({ apiPath }) => {
    if (apiPath === `proposals/${MOCK_UUID}/`) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockProposal),
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

test.describe('Proposal technical view mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('proposal_onboarding_seen', 'true');
    });
  });

  test('mode=technical shows technical intro content', {
    tag: [...PROPOSAL_TECHNICAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=technical`);
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('[data-section-type="technical_document_public"]')).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('.technical-doc-public')).toContainText('E2E propósito documento técnico');
  });

  test('mode=technical hides requirement linked to unselected module', {
    tag: [...PROPOSAL_TECHNICAL_VIEW, '@role:guest'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    await mockApi(page, buildMockHandler());
    await page.goto(`/proposal/${MOCK_UUID}?mode=technical`);
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('[data-section-type="technical_document_public"]')).toBeVisible({ timeout: 20_000 });
    // Intro panel renders first; epics (requirements text) follow stack (two "next" steps for this mock).
    const navNext = page.getByTestId('nav-next');
    await expect(navNext).toBeVisible({ timeout: 15_000 });
    await navNext.click();
    await navNext.click();
    await expect(page.getByText('E2E base scope')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('E2E linked hidden when module not selected')).toHaveCount(0);
  });
});
