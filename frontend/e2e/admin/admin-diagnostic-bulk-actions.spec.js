/**
 * E2E tests for bulk actions on the admin diagnostics list.
 *
 * Covers: selecting rows shows the batch bar, "Eliminar" confirms via modal
 * and POSTs to /diagnostics/bulk-action/, and "Cancelar" clears the selection.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_BULK_ACTIONS } from '../helpers/flow-tags.js';

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
    status: 'accepted',
    language: 'es',
    investment_amount: '5000000',
    currency: 'COP',
    view_count: 3,
    initial_sent_at: '2026-04-02T10:00:00Z',
    created_at: '2026-04-01T10:00:00Z',
    updated_at: '2026-04-15T10:00:00Z',
  },
  {
    id: 2,
    title: 'Diagnóstico Beta Inc',
    client: { name: 'Beta Inc', email: 'beta@example.com' },
    client_name: 'Beta Inc',
    status: 'draft',
    language: 'es',
    investment_amount: null,
    currency: 'COP',
    view_count: 0,
    created_at: '2026-04-10T10:00:00Z',
    updated_at: '2026-04-10T10:00:00Z',
  },
];

test.describe('Admin Diagnostic Bulk Actions', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('deleting selected diagnostics POSTs to bulk-action/ after confirmation', {
    tag: [...ADMIN_DIAGNOSTIC_BULK_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    let bulkPayload = null;

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'diagnostics/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDiagnostics) };
      }
      if (apiPath === 'diagnostics/bulk-action/' && method === 'POST') {
        bulkPayload = JSON.parse(route.request().postData() || '{}');
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ affected: bulkPayload.ids.length, action: bulkPayload.action }),
        };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/');
    await expect(page.getByLabel('Seleccionar Diagnóstico Acme Corp')).toBeVisible({ timeout: 15000 });

    await page.getByLabel('Seleccionar Diagnóstico Acme Corp').check();
    await page.getByLabel('Seleccionar Diagnóstico Beta Inc').check();

    const batchBar = page.getByTestId('diagnostics-batch-bar');
    await expect(batchBar).toBeVisible();
    await expect(batchBar).toContainText('2 seleccionados');

    await batchBar.getByRole('button', { name: 'Eliminar' }).click();

    // ConfirmModal
    await page.getByRole('button', { name: 'Eliminar', exact: true }).last().click();

    await expect(() => expect(bulkPayload).not.toBeNull()).toPass({ timeout: 5000 });
    expect(bulkPayload.action).toBe('delete');
    expect(bulkPayload.ids.sort()).toEqual([1, 2]);
  });

  test('"Cancelar" clears the selection and hides the bulk-actions bar', {
    tag: [...ADMIN_DIAGNOSTIC_BULK_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'diagnostics/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDiagnostics) };
      }
      return null;
    });

    await page.goto('/panel/diagnostics/');
    await expect(page.getByLabel('Seleccionar Diagnóstico Acme Corp')).toBeVisible({ timeout: 15000 });

    await page.getByLabel('Seleccionar Diagnóstico Acme Corp').check();
    const batchBar = page.getByTestId('diagnostics-batch-bar');
    await expect(batchBar).toBeVisible();

    await batchBar.getByRole('button', { name: 'Cancelar' }).click();
    await expect(batchBar).not.toBeVisible();
  });
});
