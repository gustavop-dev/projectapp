/**
 * E2E tests for the admin diagnostics list page.
 *
 * Covers: list renders with diagnostics, "Nuevo diagnóstico" button visible,
 * empty-state message when no diagnostics exist, search filters the visible rows.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_LIST } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const mockDiagnostics = [
  {
    id: 1,
    title: 'Diagnóstico Acme Corp',
    client_name: 'Acme Corp',
    client_email: 'acme@example.com',
    status: 'sent',
    language: 'es',
    investment_amount: '5000000',
    currency: 'COP',
    view_count: 3,
    created_at: '2026-04-01T10:00:00Z',
    updated_at: '2026-04-15T10:00:00Z',
  },
  {
    id: 2,
    title: 'Diagnóstico Beta Inc',
    client_name: 'Beta Inc',
    client_email: 'beta@example.com',
    status: 'draft',
    language: 'es',
    investment_amount: null,
    currency: 'COP',
    view_count: 0,
    created_at: '2026-04-10T10:00:00Z',
    updated_at: '2026-04-10T10:00:00Z',
  },
];

function setupMock(page, diagnostics = mockDiagnostics) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'diagnostics/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostics) };
    }
    return null;
  });
}

test.describe('Admin Diagnostic List', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders diagnostic rows and "Nuevo diagnóstico" button', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics/');

    await expect(page.getByRole('link', { name: /Nuevo diagnóstico/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Acme Corp')).toBeVisible();
    await expect(page.getByText('Beta Inc')).toBeVisible();
  });

  test('shows empty state message when no diagnostics exist', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, []);
    await page.goto('/panel/diagnostics/');

    await expect(page.getByText(/Aún no has creado diagnósticos/i)).toBeVisible({ timeout: 15000 });
  });

  test('search input filters the displayed diagnostics', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics/');

    const searchInput = page.getByTestId('diagnostics-search-input');
    await expect(searchInput).toBeVisible({ timeout: 15000 });

    await searchInput.fill('Acme');
    await expect(page.getByText('Acme Corp')).toBeVisible();
    // Beta Inc should be filtered out
    await expect(page.getByText('Beta Inc')).not.toBeVisible();
  });
});
