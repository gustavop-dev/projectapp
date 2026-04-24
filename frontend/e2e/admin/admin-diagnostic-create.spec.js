/**
 * E2E tests for admin Web App Diagnostics — create flow.
 *
 * Covers: form renders with client search and language select,
 * submit button disabled until client selected, and successful
 * creation via client-profiles search redirects to edit page.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_CREATE } from '../helpers/flow-tags.js';

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const mockClientResult = {
  id: 11,
  name: 'Acme Corp',
  full_name: 'María García',
  email: 'maria@acme.com',
  company: 'Acme Corp',
};

const mockCreatedDiagnostic = {
  id: 42,
  uuid: 'dddd-eeee-ffff-0000',
  title: 'Diagnóstico — Acme Corp',
  status: 'draft',
  documents: [],
};

test.describe('Admin Diagnostic Create', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('create page renders client search input and language select', {
    tag: [...ADMIN_DIAGNOSTIC_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      return null;
    });

    await page.goto('/panel/diagnostics/create');
    await expect(page.getByRole('heading', { name: /nuevo diagnóstico/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByPlaceholder(/buscar/i)).toBeVisible();
    await expect(page.locator('select')).toBeVisible();
  });

  test('submit button is disabled until a client is selected', {
    tag: [...ADMIN_DIAGNOSTIC_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      return null;
    });

    await page.goto('/panel/diagnostics/create');
    await expect(page.getByRole('heading', { name: /nuevo diagnóstico/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /crear diagnóstico/i })).toBeDisabled();
  });

  test('selecting a client from search results enables submit and redirects to edit', {
    tag: [...ADMIN_DIAGNOSTIC_CREATE, '@role:admin'],
  }, async ({ page }) => {
    let createCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath.includes('client-profiles/search')) {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([mockClientResult]),
        };
      }
      if (apiPath === 'diagnostics/create/' && method === 'POST') {
        createCalled = true;
        return {
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(mockCreatedDiagnostic),
        };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/create');
    await expect(page.getByRole('heading', { name: /nuevo diagnóstico/i })).toBeVisible({ timeout: 15000 });

    await page.getByPlaceholder(/buscar/i).fill('Acme');
    await page.getByText('Acme Corp').first().click();

    const submitBtn = page.getByRole('button', { name: /crear diagnóstico/i });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    await expect(() => expect(createCalled).toBe(true)).toPass({ timeout: 5000 });
    await page.waitForURL(/\/panel\/diagnostics\/42\/edit/, { timeout: 15000 });
  });
});
