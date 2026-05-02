/**
 * E2E tests for the unified Defaults shell page.
 *
 * FLOW: admin-defaults-unified
 * Covers: default proposal mode, mode switch updates URL, direct diagnostic nav,
 *         back link per mode, redirects from old routes.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DEFAULTS_UNIFIED } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const PROPOSAL_DEFAULTS = {
  id: null,
  language: 'es',
  sections_json: [
    {
      section_type: 'greeting',
      title: '👋 Saludo',
      order: 0,
      is_wide_panel: false,
      content_json: { proposalTitle: '', clientName: '', inspirationalQuote: '' },
    },
  ],
  created_at: null,
  updated_at: null,
};

const DIAGNOSTIC_DEFAULTS = {
  id: null,
  language: 'es',
  sections_json: [],
  payment_initial_pct: 60,
  payment_final_pct: 40,
  default_currency: 'COP',
  default_investment_amount: null,
  default_duration_label: '',
  expiration_days: 21,
  reminder_days: 7,
  urgency_reminder_days: 14,
  created_at: null,
  updated_at: null,
};

function buildHandler({ apiPath, method }) {
  if (apiPath === 'auth/check/') {
    return {
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
    };
  }
  if (apiPath === 'proposals/defaults/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(PROPOSAL_DEFAULTS) };
  }
  if (apiPath === 'diagnostics/defaults/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify(DIAGNOSTIC_DEFAULTS) };
  }
  if (apiPath === 'proposals/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  }
  if (apiPath === 'proposals/alerts/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  }
  if (apiPath === 'diagnostics/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  }
  if (apiPath === 'email-templates/' && method === 'GET') {
    return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  }
  return null;
}

test.describe('Admin Unified Defaults Shell', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('defaults to proposal mode on direct navigation', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/defaults', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Valores por Defecto' })).toBeVisible({ timeout: 25_000 });

    // Mode toggle renders twice (mobile inline buttons + desktop segmented pills)
    // sharing the same testId — pin to the first instance.
    const proposalBtn = page.getByTestId('defaults-mode-proposal').first();
    await expect(proposalBtn).toBeVisible();
    await expect(proposalBtn).toHaveClass(/text-text-brand/);

    const diagnosticBtn = page.getByTestId('defaults-mode-diagnostic').first();
    await expect(diagnosticBtn).not.toHaveClass(/text-text-brand/);
  });

  test('clicking Diagnóstico switch updates URL to ?mode=diagnostic', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/defaults', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Valores por Defecto' })).toBeVisible({ timeout: 25_000 });
    await page.getByTestId('defaults-mode-diagnostic').first().click();

    await expect(page).toHaveURL(/mode=diagnostic/);
    await expect(page.getByTestId('defaults-mode-diagnostic').first()).toHaveClass(/text-text-brand/);
  });

  test('direct navigation to ?mode=diagnostic activates diagnostic mode', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/defaults?mode=diagnostic', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Valores por Defecto' })).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('defaults-mode-diagnostic').first()).toHaveClass(/text-text-brand/);
    await expect(page.getByTestId('defaults-mode-proposal').first()).not.toHaveClass(/text-text-brand/);
  });

  test('back link shows "Volver a Propuestas" in proposal mode', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/defaults', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('link', { name: /Volver a Propuestas/i })).toBeVisible();
  });

  test('back link shows "Volver a Diagnósticos" in diagnostic mode', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/defaults?mode=diagnostic', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('link', { name: /Volver a Diagnósticos/i })).toBeVisible();
  });

  test('/panel/proposals/defaults redirects to /panel/defaults?mode=proposal', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/proposals/defaults', { waitUntil: 'domcontentloaded' });

    await expect(page).toHaveURL(/\/panel\/defaults/);
    await expect(page).toHaveURL(/mode=proposal/);
  });

  test('/panel/diagnostics/defaults redirects to /panel/defaults?mode=diagnostic', {
    tag: [...ADMIN_DEFAULTS_UNIFIED, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async (info) => buildHandler(info));
    await page.goto('/panel/diagnostics/defaults', { waitUntil: 'domcontentloaded' });

    await expect(page).toHaveURL(/\/panel\/defaults/);
    await expect(page).toHaveURL(/mode=diagnostic/);
  });
});
