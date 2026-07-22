/**
 * E2E tests for the admin document folder management flow.
 *
 * @flow:admin-document-folder-manage
 * Covers: FolderManagerModal create with the root-parent default, inline
 *         rename through the edit panel, delete confirmation for empty
 *         folders and the blocking panel for folders with documents.
 *         Drag-reorder is intentionally not asserted (flaky in CI).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_FOLDER_MANAGE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const emptyFolder = { id: 10, name: 'Contratos', parent: null, position: 1, document_count: 0 };
const busyFolder = { id: 11, name: 'Facturas', parent: null, position: 2, document_count: 3 };

function baseRoutes(apiPath, folders) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify(folders) };
  if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  return null;
}

async function openFolderManager(page) {
  await page.goto('/panel/documents');
  await page.getByRole('button', { name: /Gestionar/i }).click();
}

test.describe('Admin Document Folder Manage', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('creates a root folder from the manager form', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let createBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'document-folders/create/' && method === 'POST') {
        createBody = route.request().postDataJSON();
        return { status: 201, contentType: 'application/json', body: JSON.stringify({ id: 12, name: createBody.name, parent: null, position: 1, document_count: 0 }) };
      }
      return baseRoutes(apiPath, [emptyFolder]);
    });
    await openFolderManager(page);

    await page.getByPlaceholder('Nombre de la nueva carpeta...').fill('Propuestas 2026');
    await page.getByRole('button', { name: 'Crear', exact: true }).click();

    await expect.poll(() => createBody).not.toBeNull();
    expect(createBody.name).toBe('Propuestas 2026');
  });

  test('renames a folder through the inline edit panel', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let patchBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'document-folders/10/update/' && method === 'PATCH') {
        patchBody = route.request().postDataJSON();
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...emptyFolder, name: patchBody.name }) };
      }
      return baseRoutes(apiPath, [emptyFolder]);
    });
    await openFolderManager(page);

    await page.locator('button[title="Editar carpeta"]').first().click();
    const editInput = page.getByPlaceholder('Nombre de la carpeta');
    await expect(editInput).toHaveValue('Contratos');
    await editInput.fill('Contratos firmados');
    await page.getByRole('button', { name: 'Guardar', exact: true }).click();

    await expect.poll(() => patchBody).not.toBeNull();
    expect(patchBody.name).toBe('Contratos firmados');
  });

  test('deletes an empty folder after the destructive confirmation', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'document-folders/10/delete/' && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath, [emptyFolder]);
    });
    await openFolderManager(page);

    await page.locator('button[title="Eliminar carpeta"]').first().click();
    await expect(page.getByText('Eliminar "Contratos"')).toBeVisible();
    await page.getByRole('button', { name: 'Confirmar eliminación' }).click();

    await expect.poll(() => deleteCalled).toBe(true);
  });

  test('blocks deleting a folder that still holds documents', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath.startsWith('document-folders/') && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath, [busyFolder]);
    });
    await openFolderManager(page);

    await page.locator('button[title="Eliminar carpeta"]').first().click();

    await expect(page.getByRole('button', { name: 'Confirmar eliminación' })).toBeHidden();
    expect(deleteCalled).toBe(false);
  });
});
