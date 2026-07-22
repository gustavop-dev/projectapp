/**
 * E2E tests for the admin document tag management flow.
 *
 * @flow:admin-document-tags-manage
 * Covers: TagManagerModal create with name+color (POST payload asserted),
 *         inline rename committing the update PATCH, delete behind the
 *         native confirm dialog, and the cancelled-confirm branch.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_TAGS_MANAGE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockTags = [
  { id: 5, name: 'Contratos', color: 'green' },
  { id: 6, name: 'Borradores', color: 'gray' },
];

function baseRoutes(apiPath) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockTags) };
  return null;
}

async function openTagManager(page) {
  await page.goto('/panel/documents');
  await page.getByRole('button', { name: /Gestionar etiquetas/i }).click();
  await expect(page.getByRole('heading', { name: 'Gestionar etiquetas' })).toBeVisible();
}

test.describe('Admin Document Tags Manage', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('creates a tag with name and color', {
    tag: [...ADMIN_DOCUMENT_TAGS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let createBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'document-tags/create/' && method === 'POST') {
        createBody = route.request().postDataJSON();
        return { status: 201, contentType: 'application/json', body: JSON.stringify({ id: 7, ...createBody }) };
      }
      return baseRoutes(apiPath);
    });
    await openTagManager(page);

    await page.getByPlaceholder('Nombre').fill('Urgente');
    await page.locator('form select').selectOption('red');
    await page.getByRole('button', { name: 'Crear', exact: true }).click();

    await expect.poll(() => createBody).not.toBeNull();
    expect(createBody.name).toBe('Urgente');
    expect(createBody.color).toBe('red');
  });

  test('renames a tag through the inline editor', {
    tag: [...ADMIN_DOCUMENT_TAGS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let patchBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'document-tags/5/update/' && method === 'PATCH') {
        patchBody = route.request().postDataJSON();
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockTags[0], ...patchBody }) };
      }
      return baseRoutes(apiPath);
    });
    await openTagManager(page);

    await page.getByRole('listitem').filter({ hasText: 'Contratos' })
      .getByRole('button', { name: 'Editar', exact: true }).click();
    // Entering edit mode swaps the name span for the input, so the row can
    // no longer be filtered by text — the single edit input is unambiguous.
    const editInput = page.getByRole('listitem').locator('input[type="text"]');
    await expect(editInput).toHaveValue('Contratos');
    await editInput.fill('Contratos firmados');
    await page.getByRole('button', { name: 'Guardar', exact: true }).click();

    await expect.poll(() => patchBody).not.toBeNull();
    expect(patchBody.name).toBe('Contratos firmados');
  });

  test('deletes a tag after accepting the confirm dialog', {
    tag: [...ADMIN_DOCUMENT_TAGS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'document-tags/6/delete/' && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath);
    });
    await openTagManager(page);

    page.once('dialog', (dialog) => dialog.accept());
    await page.getByRole('listitem').filter({ hasText: 'Borradores' })
      .getByRole('button', { name: 'Eliminar', exact: true }).click();

    await expect.poll(() => deleteCalled).toBe(true);
  });

  test('keeps the tag when the confirm dialog is dismissed', {
    tag: [...ADMIN_DOCUMENT_TAGS_MANAGE, '@role:admin'],
  }, async ({ page }) => {
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath.startsWith('document-tags/') && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes(apiPath);
    });
    await openTagManager(page);

    page.once('dialog', (dialog) => dialog.dismiss());
    await page.getByRole('listitem').filter({ hasText: 'Borradores' })
      .getByRole('button', { name: 'Eliminar', exact: true }).click();

    await expect(
      page.getByRole('listitem').filter({ hasText: 'Borradores' }),
    ).toBeVisible();
    expect(deleteCalled).toBe(false);
  });
});
