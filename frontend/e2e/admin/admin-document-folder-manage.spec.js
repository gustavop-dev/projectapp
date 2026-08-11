/**
 * E2E tests for the admin document folder management flow.
 *
 * @flow:admin-document-folder-manage
 * Covers: FolderManagerModal create with the root-parent default, inline
 *         rename through the edit panel, delete confirmation for empty
 *         folders and the blocking panel for folders with documents, plus
 *         the sidebar delete affordance (DELETE-typed confirmation on empty
 *         folders, blocked icon on folders that still hold content).
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
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:success'],
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
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:success'],
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
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:success'],
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

    await page.getByTestId('folder-manager-delete').first().click();
    await expect(page.getByText('Eliminar "Contratos"')).toBeVisible();
    // El gestor delega en DeleteFolderModal: un solo contrato de borrado, con
    // la misma reja escrita que la papelera del sidebar.
    await page.getByTestId('delete-folder-type-input').fill('DELETE');
    await page.getByTestId('delete-folder-confirm').click();

    await expect.poll(() => deleteCalled).toBe(true);
  });

  test('blocks deleting a folder that still holds documents', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:error'],
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

    await page.getByTestId('folder-manager-delete').first().click();

    await expect(page.getByRole('button', { name: 'Confirmar eliminación' })).toBeHidden();
    expect(deleteCalled).toBe(false);
  });

  test('deletes an empty folder from the sidebar after typing DELETE', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'document-folders/10/delete/' && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath, [emptyFolder]);
    });
    await page.goto('/panel/documents');

    await page.getByRole('button', { name: 'Eliminar carpeta Contratos' }).click();

    const confirmBtn = page.getByTestId('delete-folder-confirm');
    await expect(confirmBtn).toBeDisabled();
    await page.getByTestId('delete-folder-type-input').fill('delete');
    await expect(confirmBtn).toBeDisabled();
    await page.getByTestId('delete-folder-type-input').fill('DELETE');
    await expect(confirmBtn).toBeEnabled();
    await confirmBtn.click();

    await expect.poll(() => deleteCalled).toBe(true);
  });

  test('the sidebar delete icon opens the modal, which offers archiving for a filled folder', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath.startsWith('document-folders/') && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath, [busyFolder]);
    });
    await page.goto('/panel/documents');

    // Ya no hay icono bloqueado: había que dar una salida, no explicar un muro.
    await expect(page.getByTestId('folder-delete-blocked')).toHaveCount(0);
    await page.getByTestId('folder-delete').click();

    await expect(page.getByText('Esta carpeta no se puede eliminar')).toBeVisible();
    await expect(page.getByTestId('delete-folder-archive')).toBeEnabled();
    // Sin botón destructivo muerto en esta rama.
    await expect(page.getByTestId('delete-folder-confirm')).toHaveCount(0);
    expect(deleteCalled).toBe(false);
  });

  test('surfaces the backend conflict when the folder filled up behind the icon', {
    tag: [...ADMIN_DOCUMENT_FOLDER_MANAGE, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'document-folders/10/delete/' && method === 'DELETE') {
        return {
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'La carpeta tiene 2 documento(s). Muévelos o elimínalos antes de borrarla.',
            document_count: 2,
          }),
        };
      }
      return baseRoutes(apiPath, [emptyFolder]);
    });
    await page.goto('/panel/documents');

    await page.getByRole('button', { name: 'Eliminar carpeta Contratos' }).click();
    await page.getByTestId('delete-folder-type-input').fill('DELETE');
    await page.getByTestId('delete-folder-confirm').click();

    await expect(page.getByTestId('delete-folder-error'))
      .toContainText('La carpeta tiene 2 documento(s)');
    await expect(page.getByTestId('delete-folder-confirm')).toBeVisible();
  });
});
