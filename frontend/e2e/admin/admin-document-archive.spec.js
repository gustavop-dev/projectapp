/**
 * E2E tests for the admin document/folder archive flow.
 *
 * @flow:admin-document-archive
 * Covers: archiving a document from the actions sheet, the delete modal
 *         offering archiving BEFORE the confirmation word is typed, a folder
 *         with content presenting archive as the available action instead of a
 *         dead end, the Archivados view with its date column and order control,
 *         restoring, and the archive failure branch.
 *
 * NOTE: helpers/api.js `getApiPath` strips the query string, so `documents/`
 * would otherwise swallow `documents/?archived=1`. Every route below that has
 * to tell the two scopes apart branches on the raw request URL.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_ARCHIVE } from '../helpers/flow-tags.js';

// El sidebar tiene su propio "Eliminar carpeta …", así que las acciones del
// documento se buscan siempre dentro de la hoja de acciones.
const sheetAction = (page, name) =>
  page.getByTestId('document-actions-list').getByRole('button', { name });

const json = (body) => ({
  status: 200, contentType: 'application/json', body: JSON.stringify(body),
});

const authCheck = json({ user: { username: 'admin', is_staff: true } });

const activeDocuments = [
  {
    id: 1, title: 'Contrato de Servicios', status: 'published',
    client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
    is_archived: false, archived_at: null, tag_details: [],
  },
];

const archivedDocuments = [
  {
    id: 2, title: 'Acta de cierre', status: 'draft',
    client_name: 'Vieja SAS', created_at: '2025-01-10T10:00:00Z',
    is_archived: true, archived_at: '2025-02-01T10:00:00Z',
    archived_cause: 'manual', tag_details: [],
  },
];

const activeFolders = [
  {
    id: 4, name: 'Contratos', parent: null, order: 0,
    document_count: 3, children_count: 0, is_archived: false,
  },
];

const archivedFolders = [
  {
    id: 9, name: 'Contratos 2024', parent: null, order: 0,
    document_count: 5, children_count: 0,
    is_archived: true, archived_at: '2025-02-01T10:00:00Z', archived_cause: 'manual',
  },
];

/** Routes shared by every test. `url` distinguishes the archived scope. */
function baseRoutes({ apiPath, url }) {
  const archivedScope = url.includes('archived=1');
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return json(archivedScope ? archivedDocuments : activeDocuments);
  if (apiPath === 'document-folders/') return json(archivedScope ? archivedFolders : activeFolders);
  if (apiPath === 'document-tags/') return json([]);
  return null;
}

async function openDocumentDeleteModal(page) {
  await page.goto('/panel/documents');
  await page.getByRole('row', { name: /Contrato de Servicios/i })
    .locator('button[title="Acciones"]').click();
  await sheetAction(page, /^Eliminar/).click();
  await expect(page.getByText('Eliminar documento')).toBeVisible();
}

test.describe('Admin Document Archive', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('archiving a document from the actions sheet takes it off the list', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let archived = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/1/archive/' && method === 'PATCH') {
        archived = true;
        return json({ ...activeDocuments[0], is_archived: true });
      }
      if (apiPath === 'documents/' && !url.includes('archived=1') && archived) return json([]);
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByRole('row', { name: /Contrato de Servicios/i })
      .locator('button[title="Acciones"]').click();
    await sheetAction(page, /^Archivar/).click();

    await expect(page.getByText('Documento archivado')).toBeVisible();
    expect(archived).toBe(true);
  });

  test('the delete modal offers archiving before the confirmation word is typed', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let archiveCalled = false;
    let deleteCalled = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'documents/1/archive/' && method === 'PATCH') {
        archiveCalled = true;
        return json({ ...activeDocuments[0], is_archived: true });
      }
      if (apiPath === 'documents/1/delete/' && method === 'DELETE') {
        deleteCalled = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return baseRoutes({ apiPath, url: route.request().url() });
    });
    await openDocumentDeleteModal(page);

    // La salida está disponible mientras la reja aún bloquea el destructivo.
    await expect(page.getByTestId('confirm-modal-confirm')).toBeDisabled();
    await expect(page.getByTestId('confirm-modal-secondary-hint')).toBeVisible();
    const archiveBtn = page.getByTestId('confirm-modal-secondary');
    await expect(archiveBtn).toBeEnabled();

    await archiveBtn.click();

    await expect(page.getByText('Documento archivado')).toBeVisible();
    expect(archiveCalled).toBe(true);
    expect(deleteCalled).toBe(false);
  });

  test('a folder with content offers archiving instead of a dead delete button', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let archived = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'document-folders/4/archive/' && method === 'PATCH') {
        archived = true;
        return json({
          folder: { ...activeFolders[0], is_archived: true },
          archived_folders: 0,
          archived_documents: 3,
        });
      }
      return baseRoutes({ apiPath, url: route.request().url() });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-delete').click();

    await expect(page.getByText('Esta carpeta no se puede eliminar')).toBeVisible();
    // Sin botón destructivo muerto: ese era el callejón sin salida.
    await expect(page.getByTestId('delete-folder-confirm')).toHaveCount(0);

    await page.getByTestId('delete-folder-archive').click();

    await expect(page.getByText('Carpeta archivada')).toBeVisible();
    await expect(page.getByText('Se archivaron también 3 documento(s).')).toBeVisible();
    expect(archived).toBe(true);
  });

  test('the Archivados view lists archived items with their archive date', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    let archivedRequested = false;
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('archived=1')) archivedRequested = true;
      return baseRoutes({ apiPath, url });
    });

    // quality: allow-deep-link (Archivados no es una ruta propia sino un scope
    // de /panel/documents; el camino real del usuario —el click en la entrada
    // del sidebar— sí se recorre justo debajo.)
    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();

    await expect(page.getByRole('table').getByText('Acta de cierre')).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Archivado' })).toBeVisible();
    await expect(page.getByTestId('doc-archived-at')).toContainText('2025');
    expect(archivedRequested).toBe(true);
  });

  test('picking Más antiguos refetches the archived list oldest-first', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let oldestRequested = false;
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('order=oldest')) oldestRequested = true;
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await expect(page.getByRole('table').getByText('Acta de cierre')).toBeVisible();

    await page.getByTestId('archived-order-oldest').click();

    await expect.poll(() => oldestRequested).toBe(true);
  });

  test('restoring an archived document takes it out of the archived list', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let restored = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/2/unarchive/' && method === 'PATCH') {
        restored = true;
        return json({ ...archivedDocuments[0], is_archived: false, archived_at: null });
      }
      if (apiPath === 'documents/' && url.includes('archived=1') && restored) return json([]);
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await page.getByRole('row', { name: /Acta de cierre/i })
      .locator('button[title="Acciones"]').click();
    await sheetAction(page, /^Restaurar/).click();

    await expect(page.getByText('Documento restaurado')).toBeVisible();
    expect(restored).toBe(true);
  });

  test('shows the error toast when archiving a document fails', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'documents/1/archive/' && method === 'PATCH') {
        return { status: 500, contentType: 'application/json', body: '{}' };
      }
      return baseRoutes({ apiPath, url: route.request().url() });
    });

    await page.goto('/panel/documents');
    await page.getByRole('row', { name: /Contrato de Servicios/i })
      .locator('button[title="Acciones"]').click();
    await sheetAction(page, /^Archivar/).click();

    // exact: el toast repite casi el mismo texto en título y detalle.
    await expect(page.getByText('No se pudo archivar el documento', { exact: true })).toBeVisible();
  });
});
