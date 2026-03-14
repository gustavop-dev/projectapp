/**
 * E2E tests for admin proposal defaults configuration flow.
 *
 * FLOW: admin-proposal-defaults-config
 * Covers: navigate to defaults page, view sections, edit a section,
 * save all changes, reset to hardcoded defaults.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DEFAULTS_CONFIG } from '../helpers/flow-tags.js';

const MOCK_DEFAULTS_ES = {
  id: null,
  language: 'es',
  sections_json: [
    {
      section_type: 'greeting',
      title: '👋 Saludo',
      order: 0,
      is_wide_panel: false,
      content_json: { proposalTitle: '', clientName: '', inspirationalQuote: 'Design is how it works.' },
    },
    {
      section_type: 'executive_summary',
      title: '📋 Resumen Ejecutivo',
      order: 1,
      is_wide_panel: true,
      content_json: { index: '02', title: 'Resumen Ejecutivo', paragraphs: [], highlights: [] },
    },
  ],
  created_at: null,
  updated_at: null,
};

const MOCK_SAVED_RESPONSE = {
  id: 1,
  language: 'es',
  sections_json: MOCK_DEFAULTS_ES.sections_json,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T12:00:00Z',
};

function buildApiHandler(apiPath, method) {
  if (apiPath === 'auth/check/') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
  }
  if (apiPath === 'proposals/defaults/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DEFAULTS_ES) };
  }
  if (apiPath === 'proposals/defaults/' && method === 'PUT') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SAVED_RESPONSE) };
  }
  if (apiPath === 'proposals/defaults/reset/' && method === 'POST') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'reset', deleted: true }) };
  }
  if (apiPath === 'email-templates/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  }
  return null;
}

test.describe('Admin Proposal Defaults Config', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8200, role: 'admin', is_staff: true } });
  });

  test('renders defaults page with sections list', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=sections');

    // Page title renders
    await expect(page.locator('h1')).toContainText('Valores por Defecto', { timeout: 15000 });

    // Language buttons render
    await expect(page.getByRole('button', { name: 'Español' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'English' })).toBeVisible();

    // Sections render
    await expect(page.locator('text=👋 Saludo')).toBeVisible();
    await expect(page.locator('text=📋 Resumen Ejecutivo')).toBeVisible();
  });

  test('expands section and shows SectionEditor', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=sections');
    await page.waitForLoadState('networkidle');

    // Click on greeting section header to expand
    await page.locator('text=👋 Saludo').click();

    // SectionEditor should render with title input
    await expect(page.locator('[data-testid="section-editor"]')).toBeVisible();
  });

  test('save button is disabled when no changes', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=sections');
    await page.waitForLoadState('networkidle');

    const saveBtn = page.getByRole('button', { name: 'Guardar Todos los Cambios' });
    await expect(saveBtn).toBeDisabled();
  });

  test('shows reset confirmation modal', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => buildApiHandler(apiPath, method));
    await page.goto('/panel/proposals/defaults?tab=sections');
    await page.waitForLoadState('networkidle');

    // Click reset button
    await page.getByRole('button', { name: 'Restaurar valores originales' }).click();

    // Confirmation modal renders
    await expect(page.locator('text=¿Restaurar valores originales?')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sí, restaurar' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancelar' })).toBeVisible();
  });

  test('back link navigates to proposals list', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_CONFIG, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method: _method }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/defaults/') return { status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DEFAULTS_ES) };
      if (apiPath === 'proposals/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'proposals/alerts/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'proposals/dashboard/') return { status: 200, contentType: 'application/json', body: JSON.stringify({}) };
      return null;
    });
    await page.goto('/panel/proposals/defaults');
    await page.waitForLoadState('networkidle');

    // Click back link
    await page.locator('text=Volver a Propuestas').click();
    await page.waitForURL('**/panel/proposals**');
  });
});
