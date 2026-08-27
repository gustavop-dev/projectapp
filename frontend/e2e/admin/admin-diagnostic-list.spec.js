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
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics/');

    await expect(page.getByRole('main').getByRole('link', { name: /Nuevo diagnóstico/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('diagnostic-open-1')).toBeVisible();
    await expect(page.getByTestId('diagnostic-open-2')).toBeVisible();
  });

  test('renders the leading menu control track', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin', '@outcome:display', '@responsive:commercial'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display contract: control order, blank heading and fixed width are the observable outcome)
    // quality: allow-deep-link (the list navigation path is covered by the owning flow; this test isolates table layout)
    await setupMock(page);
    await page.goto('/panel/diagnostics/');

    const actionsHeader = page.getByTestId('diagnostic-actions-header');
    await expect(actionsHeader).toBeVisible({ timeout: 15000 });
    const leadingHeaders = await actionsHeader.evaluate((header) => (
      Array.from(header.parentElement.children).slice(0, 3).map((cell) => ({
        testId: cell.getAttribute('data-testid'),
        label: cell.getAttribute('aria-label'),
        text: cell.textContent.trim(),
        hasCheckbox: Boolean(cell.querySelector('input[type="checkbox"]')),
      }))
    ));
    expect(leadingHeaders).toEqual([
      { testId: null, label: null, text: '', hasCheckbox: true },
      { testId: 'diagnostic-actions-header', label: 'Acciones', text: '', hasCheckbox: false },
      { testId: null, label: null, text: 'Cliente', hasCheckbox: false },
    ]);
    await expect(actionsHeader).toHaveCSS('width', '56px');
  });

  test('opens row actions without navigating', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics/');

    const actionsButton = page.getByRole('button', { name: 'Acciones de Diagnóstico Acme Corp' });
    await expect(actionsButton).toBeVisible({ timeout: 15000 });
    const listUrl = page.url();
    await actionsButton.click();

    await expect(page).toHaveURL(listUrl);
    await expect(page.getByRole('heading', { name: 'Diagnóstico Acme Corp' })).toBeVisible();
  });

  test('shows empty state message when no diagnostics exist', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin', '@outcome:display', '@responsive:commercial'],
  }, async ({ page }) => {
    await setupMock(page, []);
    await page.goto('/panel/diagnostics/');

    await expect(page.getByText(/Aún no has creado diagnósticos/i)).toBeVisible({ timeout: 15000 });
  });

  test('search input filters the displayed diagnostics', {
    tag: [...ADMIN_DIAGNOSTIC_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/diagnostics/');

    const searchInput = page.getByTestId('diagnostics-search-input');
    await expect(searchInput).toBeVisible({ timeout: 15000 });

    await searchInput.fill('Acme');
    await expect(page.getByTestId('diagnostic-open-1')).toBeVisible();
    // Beta Inc should be filtered out
    await expect(page.getByTestId('diagnostic-open-2')).toHaveCount(0);
  });
});
