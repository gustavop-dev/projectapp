/**
 * E2E tests for the admin document rename flow.
 *
 * @flow:admin-document-rename
 * Covers: RenameDocumentModal opening prefilled from the actions sheet,
 *         PATCH /api/documents/<id>/update/ with the new title, and the
 *         inline error branch keeping the modal open.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_RENAME } from '../helpers/flow-tags.js';

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

async function openRenameModal(page) {
  await page.goto('/panel/documents');
  await page.getByRole('row', { name: /Contrato de Servicios/i }).locator('button[title="Acciones"]').click();
  await page.getByRole('button', { name: /Renombrar/i }).click();
}

test.describe('Admin Document Rename', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('opens the modal prefilled with the current title', {
    tag: [...ADMIN_DOCUMENT_RENAME, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => baseRoutes(apiPath));
    await openRenameModal(page);

    await expect(page.getByPlaceholder('Nombre del documento')).toHaveValue('Contrato de Servicios');
  });

  test('saves the new title through the update PATCH', {
    tag: [...ADMIN_DOCUMENT_RENAME, '@role:admin'],
  }, async ({ page }) => {
    let patchBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        patchBody = route.request().postDataJSON();
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDocuments[0], title: 'Contrato 2026' }) };
      }
      return baseRoutes(apiPath);
    });
    await openRenameModal(page);

    await page.getByPlaceholder('Nombre del documento').fill('Contrato 2026');
    await page.getByRole('button', { name: 'Guardar', exact: true }).click();

    await expect(page.getByPlaceholder('Nombre del documento')).toBeHidden();
    expect(patchBody.title).toBe('Contrato 2026');
  });

  test('keeps the modal open with an inline error when the PATCH fails', {
    tag: [...ADMIN_DOCUMENT_RENAME, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        return { status: 500, contentType: 'application/json', body: '{}' };
      }
      return baseRoutes(apiPath);
    });
    await openRenameModal(page);

    await page.getByPlaceholder('Nombre del documento').fill('Contrato 2026');
    await page.getByRole('button', { name: 'Guardar', exact: true }).click();

    await expect(page.getByPlaceholder('Nombre del documento')).toBeVisible();
  });
});
