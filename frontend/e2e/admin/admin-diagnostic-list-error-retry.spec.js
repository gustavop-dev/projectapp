/**
 * E2E test for the diagnostics list load-error + retry flow.
 *
 * A failed GET /diagnostics/ renders a dedicated error state (distinct from the
 * empty state) with a "Reintentar" button; retrying after the API recovers
 * shows the table.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_LIST_ERROR_RETRY } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const mockDiagnostics = [
  {
    id: 1,
    title: 'Diagnóstico Acme Corp',
    client: { name: 'Acme Corp', email: 'acme@example.com' },
    client_name: 'Acme Corp',
    status: 'sent',
    language: 'es',
    investment_amount: '5000000',
    currency: 'COP',
    view_count: 3,
    created_at: '2026-04-01T10:00:00Z',
    updated_at: '2026-04-15T10:00:00Z',
  },
];

test.describe('Admin Diagnostic List — load error & retry', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('shows the error state on a failed load and recovers on retry', {
    tag: [...ADMIN_DIAGNOSTIC_LIST_ERROR_RETRY, '@role:admin'],
  }, async ({ page }) => {
    let listCalls = 0;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'diagnostics/') {
        listCalls += 1;
        if (listCalls === 1) {
          return { status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'error' }) };
        }
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDiagnostics) };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/');

    const errorState = page.getByTestId('diagnostics-error-state');
    await expect(errorState).toBeVisible({ timeout: 15000 });

    await errorState.getByRole('button', { name: /Reintentar/i }).click();

    await expect(errorState).not.toBeVisible();
    await expect(page.getByTestId('diagnostic-row-1')).toBeVisible({ timeout: 10000 });
  });
});
