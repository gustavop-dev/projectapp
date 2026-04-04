/**
 * E2E tests for admin sending branded and proposal emails from proposal edit page.
 *
 * Covers: Correos tab visibility for negotiating proposals, composer sections render,
 * Enviar correo tab visibility for sent proposals, tab hidden for draft proposals.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_SEND_BRANDED_EMAIL, ADMIN_SEND_PROPOSAL_EMAIL } from '../helpers/flow-tags.js';

const PROPOSAL_ID = 7;
const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const futureDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

function makeProposal(overrides = {}) {
  return {
    id: PROPOSAL_ID,
    uuid: 'email-test-uuid-1234-5678-abcdef',
    title: 'Email Test Proposal',
    client_name: 'Email Client',
    client_email: 'client@emailtest.com',
    status: 'negotiating',
    language: 'es',
    total_investment: '8000000',
    currency: 'COP',
    view_count: 3,
    sent_at: '2026-03-01T10:00:00Z',
    expires_at: futureDate,
    is_active: true,
    sections: [
      { id: 10, section_type: 'greeting', title: 'Bienvenido', order: 0, is_enabled: true, content_json: { clientName: 'Email Client' } },
    ],
    requirement_groups: [],
    change_logs: [],
    ...overrides,
  };
}

const emailDefaults = {
  greeting: 'Hola Email Client',
  footer: 'Quedamos atentos a tus comentarios.\nUn abrazo, el equipo de Project App.',
};

const emptyHistory = { results: [], total: 0, page: 1, has_next: false };

function emailApiRoutes(proposal) {
  return async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === `proposals/${PROPOSAL_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposal) };
    }
    if (apiPath.includes('/branded-email/defaults/') || apiPath.includes('/proposal-email/defaults/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(emailDefaults) };
    }
    if (apiPath.includes('/branded-email/history/') || apiPath.includes('/proposal-email/history/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(emptyHistory) };
    }
    return null;
  };
}

test.describe('Admin Proposal Email — Branded', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('branded email tab is visible for negotiating proposal', {
    tag: [...ADMIN_SEND_BRANDED_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    const proposal = makeProposal({ status: 'negotiating' });
    await mockApi(page, emailApiRoutes(proposal));

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const correosTab = page.getByRole('button', { name: /Correos/i });
    await expect(correosTab).toBeVisible({ timeout: 15000 });
  });

  test('branded email composer renders sections editor', {
    tag: [...ADMIN_SEND_BRANDED_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    const proposal = makeProposal({ status: 'negotiating' });
    await mockApi(page, emailApiRoutes(proposal));

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const correosTab = page.getByRole('button', { name: /Correos/i });
    await expect(correosTab).toBeVisible({ timeout: 15000 });
    await correosTab.click();

    // Composer should show recipient, subject, and section inputs
    await expect(page.getByPlaceholder(/correo@ejemplo/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByPlaceholder(/Asunto del correo/i)).toBeVisible();
    await expect(page.getByText('Secciones del correo')).toBeVisible();
    await expect(page.getByText('Agregar sección')).toBeVisible();
  });
});

test.describe('Admin Proposal Email — Proposal Mode', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('proposal email tab is visible for sent proposal', {
    tag: [...ADMIN_SEND_PROPOSAL_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    const proposal = makeProposal({ status: 'sent' });
    await mockApi(page, emailApiRoutes(proposal));

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    const sendEmailTab = page.getByRole('button', { name: /Enviar correo/i });
    await expect(sendEmailTab).toBeVisible({ timeout: 15000 });
  });

  test('proposal email tab is not visible for draft proposal', {
    tag: [...ADMIN_SEND_PROPOSAL_EMAIL, '@role:admin'],
  }, async ({ page }) => {
    test.setTimeout(60_000);
    const proposal = makeProposal({ status: 'draft' });
    await mockApi(page, emailApiRoutes(proposal));

    await page.goto(`/panel/proposals/${PROPOSAL_ID}/edit`);

    // Wait for the page to load by checking another element is visible
    await expect(page.locator('main')).toBeVisible({ timeout: 15000 });

    const sendEmailTab = page.getByRole('button', { name: /Enviar correo/i });
    await expect(sendEmailTab).toHaveCount(0);
  });
});
