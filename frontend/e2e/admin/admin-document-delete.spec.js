/**
 * E2E tests for the admin document delete flow.
 *
 * @flow:admin-document-delete
 * Covers: delete confirmation through ConfirmModal firing DELETE
 *         /api/documents/<id>/delete/ with a success toast, the cancel
 *         branch keeping the document, and the error toast branch.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_DELETE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDocuments = [
  {
    id: 1, title: 'Contrato de Servicios', status: 'published',
    client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
  },
];

function baseRoutes(apiPath) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
  if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  return null;
}

async function openDeleteConfirm(page) {
  await page.goto('/panel/documents');
  await page.getByRole('row', { name: /Contrato de Servicios/i }).locator('button[title="Acciones"]').click();
  await page.getByRole('button', { name: /Eliminar/i }).click();
  await expect(page.getByText('Eliminar documento')).toBeVisible();
}

test.describe('Admin Document Delete', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('confirming deletes the document and shows the success toast', {
    tag: [...ADMIN_DOCUMENT_DELETE, '@role:admin'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/delete/' && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath);
    });
    await openDeleteConfirm(page);

    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Documento eliminado')).toBeVisible();
    expect(deleteCalled).toBe(true);
  });

  test('cancelling keeps the document without calling the API', {
    tag: [...ADMIN_DOCUMENT_DELETE, '@role:admin'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/delete/' && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath);
    });
    await openDeleteConfirm(page);

    await page.getByRole('button', { name: 'Cancelar', exact: true }).click();

    await expect(page.getByText('Eliminar documento')).toBeHidden();
    await expect(page.getByRole('table').getByText('Contrato de Servicios')).toBeVisible();
    expect(deleteCalled).toBe(false);
  });

  test('shows the error toast when the DELETE fails', {
    tag: [...ADMIN_DOCUMENT_DELETE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/delete/' && method === 'DELETE') {
        return { status: 500, contentType: 'application/json', body: '{}' };
      }
      return baseRoutes(apiPath);
    });
    await openDeleteConfirm(page);

    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('No se pudo eliminar el documento', { exact: true })).toBeVisible();
  });
});
