/**
 * E2E tests for configuring the default slug pattern from /panel/defaults?mode=proposal.
 *
 * @flow:admin-proposal-defaults-slug-pattern
 *
 * Covers: input prefilled from server, live preview reacts to typing,
 * saving PUTs proposals/defaults/ with the new default_slug_pattern.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DEFAULTS_SLUG_PATTERN } from '../helpers/flow-tags.js';

const baseDefaults = {
  id: 1,
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
  default_slug_pattern: '{client_name}',
  default_expiration_days: 21,
  default_reminder_days: 7,
  default_urgency_reminder_days: 14,
  created_at: null,
  updated_at: null,
};

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildHandler(initialPattern, captureRef) {
  return async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === 'proposals/defaults/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...baseDefaults, default_slug_pattern: initialPattern }),
      };
    }
    if (apiPath === 'proposals/defaults/' && method === 'PUT') {
      const raw = route.request().postData();
      if (raw) captureRef.payload = JSON.parse(raw);
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...baseDefaults,
          ...(captureRef.payload || {}),
        }),
      };
    }
    if (apiPath === 'email-templates/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

test.describe('Admin Proposal — Defaults Slug Pattern', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8800, role: 'admin', is_staff: true },
    });
  });

  test('slug pattern input is prefilled from server defaults', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_SLUG_PATTERN, '@role:admin'],
  }, async ({ page }) => {
    const captureRef = { payload: null };
    await mockApi(page, buildHandler('{client_name}', captureRef));

    await page.goto('/panel/defaults?mode=proposal', { waitUntil: 'domcontentloaded' });

    const input = page.getByTestId('defaults-slug-pattern');
    await expect(input).toBeVisible({ timeout: 15000 });
    await expect(input).toHaveValue('{client_name}');
  });

  test('live preview reflects edits to the pattern input', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_SLUG_PATTERN, '@role:admin'],
  }, async ({ page }) => {
    const captureRef = { payload: null };
    await mockApi(page, buildHandler('{client_name}', captureRef));

    await page.goto('/panel/defaults?mode=proposal', { waitUntil: 'domcontentloaded' });

    const input = page.getByTestId('defaults-slug-pattern');
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill('promo-2026');

    await expect(page.getByText('/proposal/promo-2026')).toBeVisible({ timeout: 5000 });
  });

  test('saving sends PUT to proposals/defaults/ with the new pattern', {
    tag: [...ADMIN_PROPOSAL_DEFAULTS_SLUG_PATTERN, '@role:admin'],
  }, async ({ page }) => {
    const captureRef = { payload: null };
    await mockApi(page, buildHandler('{client_name}', captureRef));

    await page.goto('/panel/defaults?mode=proposal', { waitUntil: 'domcontentloaded' });

    const input = page.getByTestId('defaults-slug-pattern');
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill('{client_name}-{year}');

    await page.getByRole('button', { name: /Guardar Vista General/ }).click();

    await expect(() => expect(captureRef.payload).not.toBeNull()).toPass({ timeout: 5000 });
    expect(captureRef.payload.default_slug_pattern).toBe('{client_name}-{year}');
  });
});
