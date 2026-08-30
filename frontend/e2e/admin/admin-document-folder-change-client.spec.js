/**
 * E2E tests for reassigning a folder's client.
 *
 * @flow:admin-document-folder-change-client
 * Covers: el PATCH plano rebotando con 409 `folder_has_content` y abriendo la
 *         cascada, el preview nombrando lo que pasa y lo que NO se toca, el
 *         modo que hay que elegir siempre, y el apply mandando de vuelta los
 *         ids del plan como token.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_FOLDER_CHANGE_CLIENT } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const json = (body, status = 200) => ({
  status, contentType: 'application/json', body: JSON.stringify(body),
});

const folder = {
  id: 10,
  name: 'Kore',
  parent: null,
  document_count: 2,
  children_count: 1,
  active_document_count: 2,
  active_children_count: 1,
  client: 7,
  client_display_name: 'Kore SAS',
};

const navigationPayload = {
  totals: {
    active: { folders: 1, documents: 2 },
    archived: { folders: 0, documents: 0 },
  },
  unassigned: {
    project: {
      active: { folders: 1, documents: 2 },
      archived: { folders: 0, documents: 0 },
    },
    client: {
      active: { folders: 0, documents: 0 },
      archived: { folders: 0, documents: 0 },
    },
  },
  projects: [],
  clients: [{
    id: 7,
    name: 'Kore SAS',
    is_inactive: false,
    catalog_bucket: 'active',
    counts: {
      active: { folders: 1, documents: 2 },
      archived: { folders: 0, documents: 0 },
    },
  }],
};

const preview = {
  folder: { id: 10, name: 'Kore' },
  current_client: { profile_id: 7, name: 'Kore SAS' },
  new_client: { profile_id: 9, name: 'Ana Pérez' },
  folders_move: [{ id: 11, name: 'Diseño' }],
  folders_foreign: [],
  documents_move: [{ id: 1, title: 'Contrato marco' }],
  documents_blocked: [
    { id: 3, title: 'CC-014', reason: 'Es una cuenta de cobro ya emitida.' },
  ],
  documents_foreign: [],
  folder_ids: [11],
  document_ids: [1],
  totals: { folders: 1, documents: 1, blocked: 1, foreign: 0, foreign_folders: 0 },
};

function baseRoutes(apiPath) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'accounts/panel-preferences/documents/') {
    return json({ navigation_mode: 'project' });
  }
  if (apiPath === 'documents/navigation/') return json(navigationPayload);
  if (apiPath === 'documents/') return json([]);
  if (apiPath === 'document-folders/') return json([folder]);
  if (apiPath === 'document-tags/') return json([]);
  if (apiPath.startsWith('proposals/client-profiles/search/')) {
    return json([{ id: 9, name: 'Ana Pérez', email: 'ana@example.com' }]);
  }
  if (apiPath.startsWith('proposals/client-profiles/')) return json([]);
  if (apiPath.startsWith('projects/')) return json([]);
  return null;
}

/** Elige a Ana en el autocompletado del formulario de la carpeta. */
async function pickAnotherClient(page) {
  await page.getByTestId('folder-form-client').fill('Ana');
  const option = page.getByTestId('client-autocomplete-option-9');
  await expect(option).toBeInViewport({ ratio: 1 });
  await option.click();
}

/** Entra por el catálogo del cliente; la carpeta asignada no se duplica como huérfana. */
async function openFolderForm(page) {
  await page.getByTestId('documents-mode-client').click();
  await page.getByTestId('documents-navigation-client-7').click();
  const row = page.getByRole('row', { name: /Kore/i });
  await expect(row).toBeVisible();
  await row.click();
  await page.getByTestId('folder-header-edit').click();
}

test.describe('Admin Document Folder Change Client', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('a folder with content sends its client change to the cascade', {
    tag: [...ADMIN_DOCUMENT_FOLDER_CHANGE_CLIENT, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'document-folders/10/update/' && method === 'PATCH') {
        return json({
          error: 'La carpeta tiene contenido.',
          code: 'folder_has_content',
        }, 409);
      }
      if (apiPath === 'document-folders/10/change-client/preview/') {
        return json(preview);
      }
      return baseRoutes(apiPath);
    });
    await page.goto('/panel/documents');

    await openFolderForm(page);
    await pickAnotherClient(page);
    await page.getByTestId('folder-form-save').click();

    // El formulario no se traga el 409: abre el camino que sí sabe decir a
    // qué afecta el cambio, ya apuntando a la carpeta en cuestión.
    await expect(page.getByTestId('folder-change-client-modal'))
      .toContainText('Cambiar el cliente de "Kore"');
    await expect(page.getByTestId('folder-form-modal')).toHaveCount(0);
  });

  test('the preview names what moves and what will not be touched', {
    tag: [...ADMIN_DOCUMENT_FOLDER_CHANGE_CLIENT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'document-folders/10/update/' && method === 'PATCH') {
        return json({ code: 'folder_has_content' }, 409);
      }
      if (apiPath === 'document-folders/10/change-client/preview/') {
        return json(preview);
      }
      return baseRoutes(apiPath);
    });
    await page.goto('/panel/documents');
    await openFolderForm(page);
    await pickAnotherClient(page);
    await page.getByTestId('folder-form-save').click();

    await expect(page.getByTestId('folder-change-client-preview'))
      .toContainText('Contrato marco');
    await expect(page.getByTestId('folder-change-client-blocked'))
      .toContainText('CC-014');
    // Sin modo elegido no se confirma: la pregunta se hace cada vez.
    await expect(page.getByTestId('folder-change-client-confirm')).toBeDisabled();
  });

  test('confirming sends back the plan it showed', {
    tag: [...ADMIN_DOCUMENT_FOLDER_CHANGE_CLIENT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let applyBody = null;
    await mockApi(page, async ({ route, apiPath, method }) => {
      if (apiPath === 'document-folders/10/update/' && method === 'PATCH') {
        return json({ code: 'folder_has_content' }, 409);
      }
      if (apiPath === 'document-folders/10/change-client/preview/') {
        return json(preview);
      }
      if (apiPath === 'document-folders/10/change-client/' && method === 'POST') {
        applyBody = route.request().postDataJSON();
        return json({
          folder: { ...folder, client: 9, client_display_name: 'Ana Pérez' },
          moved: { folders: 1, documents: 1 },
          skipped: { blocked: 1, foreign: 0, foreign_folders: 0 },
        });
      }
      return baseRoutes(apiPath);
    });
    await page.goto('/panel/documents');
    await openFolderForm(page);
    await pickAnotherClient(page);
    await page.getByTestId('folder-form-save').click();
    await expect(page.getByTestId('folder-change-client-preview')).toBeVisible();

    await page.getByTestId('folder-change-client-mode')
      .getByText('Pasa también el contenido').click();
    await page.getByTestId('folder-change-client-confirm').click();

    await expect.poll(() => applyBody).not.toBeNull();
    expect(applyBody.mode).toBe('propagate');
    expect(applyBody.document_ids).toEqual([1]);
    expect(applyBody.folder_ids).toEqual([11]);
  });
});
