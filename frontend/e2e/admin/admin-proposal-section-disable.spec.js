/**
 * E2E tests for toggling section visibility (is_enabled) on the proposal edit page.
 *
 * @flow:admin-proposal-section-disable
 *
 * Covers: clicking the "Visible" checkbox on a section row PATCHes
 * /api/proposals/sections/<id>/update/ with { is_enabled: false } and
 * the section row reflects the disabled state in admin UI.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_SECTION_DISABLE } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 5;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function makeProposal(overrides = {}) {
  return {
    id: PROPOSAL_ID,
    uuid: 'cccc1111-2222-3333-4444-555566667777',
    slug: 'section-toggle-test',
    title: 'Section Toggle Test',
    client_name: 'Toggle Client',
    status: 'draft',
    language: 'es',
    total_investment: '5000000',
    currency: 'COP',
    sections: [
      { id: 11, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true, content_json: { clientName: 'Toggle Client' } },
      { id: 12, section_type: 'executive_summary', title: 'Resumen', order: 1, is_enabled: true, content_json: {} },
      { id: 13, section_type: 'investment', title: 'Inversión', order: 2, is_enabled: true, content_json: {} },
    ],
    requirement_groups: [],
    change_logs: [],
    proposal_documents: [],
    ...overrides,
  };
}

test.describe('Admin Proposal — Section Disable Toggle', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 7700, role: 'admin', is_staff: true },
    });
  });

  test('clicking the Visible checkbox PATCHes the section with is_enabled=false', {
    tag: [...ADMIN_PROPOSAL_SECTION_DISABLE, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(makeProposal()) };
      }
      if (apiPath === 'proposals/sections/12/update/' && (method === 'PATCH' || method === 'PUT' || method === 'POST')) {
        const raw = route.request().postData();
        if (raw) capturedPayload = JSON.parse(raw);
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ id: 12, section_type: 'executive_summary', is_enabled: false }),
        };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=sections`, { waitUntil: 'domcontentloaded' });

    const sectionHeader = page.getByTestId('section-header-executive_summary');
    await expect(sectionHeader).toBeVisible({ timeout: 15000 });

    const visibleCheckbox = sectionHeader.locator('input[type="checkbox"]');
    await expect(visibleCheckbox).toBeChecked();
    await visibleCheckbox.click();

    await expect(() => expect(capturedPayload).not.toBeNull()).toPass({ timeout: 5000 });
    expect(capturedPayload.is_enabled).toBe(false);
  });

  test('disabled section starts unchecked when is_enabled=false from server', {
    tag: [...ADMIN_PROPOSAL_SECTION_DISABLE, '@role:admin'],
  }, async ({ page }) => {
    const proposal = makeProposal();
    proposal.sections[1].is_enabled = false;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
      }
      return null;
    });

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit?tab=sections`, { waitUntil: 'domcontentloaded' });

    const sectionHeader = page.getByTestId('section-header-executive_summary');
    await expect(sectionHeader).toBeVisible({ timeout: 15000 });

    const visibleCheckbox = sectionHeader.locator('input[type="checkbox"]');
    await expect(visibleCheckbox).not.toBeChecked();
  });
});
