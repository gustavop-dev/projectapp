/**
 * E2E tests for the admin document/folder archive flow.
 *
 * @flow:admin-document-archive
 * Covers: archiving a document from the actions sheet and from the sidebar row,
 *         the delete modal offering archiving BEFORE the confirmation word is
 *         typed, the delete icon going inert for a folder with content, the
 *         Archivados view as a NAVIGABLE tree (folder as container, not
 *         siblings), restoring an item from inside an archived folder and the
 *         container chain that comes back with it, the state filter, the global
 *         search reaching archived items, and the archive failure branch.
 *
 * NOTE: helpers/api.js `getApiPath` strips the query string, so `documents/`
 * would otherwise swallow `documents/?scope=archived`. Every route below that
 * has to tell the scopes apart branches on the raw request URL.
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
    document_count: 3, children_count: 0,
    active_document_count: 3, active_children_count: 0,
    archived_document_count: 0, archived_children_count: 0,
    is_archived: false,
  },
  // Estado mixto: activa por fuera, con archivados dentro — lo que deja una
  // restauración por cadena.
  {
    id: 5, name: 'temp', parent: null, order: 1,
    document_count: 0, children_count: 0,
    active_document_count: 0, active_children_count: 0,
    archived_document_count: 2, archived_children_count: 0,
    is_archived: false,
  },
];

const archivedFolders = [
  {
    id: 9, name: 'Contratos 2024', parent: null, order: 0,
    document_count: 5, children_count: 1,
    active_document_count: 0, active_children_count: 0,
    archived_document_count: 5, archived_children_count: 1,
    is_archived: true, archived_at: '2025-02-01T10:00:00Z', archived_cause: 'manual',
  },
  // Arrastrada por la cascada: NO debe aparecer junto a su padre en la cima.
  {
    id: 10, name: 'Anexos', parent: 9, order: 0,
    document_count: 1, children_count: 0,
    active_document_count: 0, active_children_count: 0,
    archived_document_count: 1, archived_children_count: 0,
    is_archived: true, archived_at: '2025-02-01T10:00:00Z', archived_cause: 'folder',
  },
];

const counts = {
  documents: { active: 1, archived: 1, unfiled_active: 1, unfiled_archived: 0 },
  folders: { active: 2, archived: 2 },
};

/** Routes shared by every test. `url` distinguishes the requested scope. */
function baseRoutes({ apiPath, url }) {
  const archivedScope = url.includes('scope=archived');
  const mixedScope = url.includes('scope=all');
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/counts/') return json(counts);
  if (apiPath === 'documents/') {
    if (mixedScope) return json([...activeDocuments, ...archivedDocuments]);
    return json(archivedScope ? archivedDocuments : activeDocuments);
  }
  if (apiPath === 'document-folders/') {
    if (mixedScope && url.includes('search=')) return json([]);
    // El store pide siempre el árbol completo: la jerarquía archivada necesita
    // saber si el padre de una carpeta está activo o archivado.
    return json([...activeFolders, ...archivedFolders]);
  }
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
      if (apiPath === 'documents/' && url.includes('scope=active') && archived) return json([]);
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

  test('a folder with content archives from its own row, with delete gone inert', {
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
    const row = page.getByRole('listitem').filter({ hasText: 'Contratos' });

    // Eliminar es imposible con contenido — el backend responde 409 —, así que
    // el ícono lo dice en vez de llevar a un modal sin salida.
    await expect(row.getByTestId('folder-delete')).toBeDisabled();
    // El tooltip sólo aparece al pasar por encima; es donde vive la explicación.
    await row.getByTestId('folder-delete').hover();
    await expect(row.getByText(/No se puede eliminar/)).toBeVisible();

    await row.getByTestId('folder-archive').click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Carpeta archivada')).toBeVisible();
    await expect(page.getByText('Se archivaron también 3 documento(s).')).toBeVisible();
    expect(archived).toBe(true);
  });

  test('an archived folder shows up as a container, not beside its documents', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => (
      baseRoutes({ apiPath, url: route.request().url() })
    ));

    // quality: allow-deep-link (Archivados no es una ruta propia sino un scope
    // de /panel/documents; el camino del usuario —el click en la entrada del
    // sidebar— sí se recorre en la línea siguiente.)
    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();

    const table = page.getByRole('table');
    await expect(table.getByText('Contratos 2024')).toBeVisible();
    // La subcarpeta que arrastró la cascada vive DENTRO, no al lado.
    await expect(table.getByText('Anexos')).toHaveCount(0);
  });

  test('an archived folder can be entered and navigated like an active one', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const nested = [{
      id: 21, title: 'Anexo firmado', status: 'draft', client_name: 'Vieja SAS',
      created_at: '2025-01-10T10:00:00Z', is_archived: true,
      archived_at: '2025-02-01T10:00:00Z', folder: 9, tag_details: [],
    }];
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('folder=9')) return json(nested);
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await page.getByRole('row', { name: /Contratos 2024/i }).click();

    await expect(page.getByRole('table').getByText('Anexo firmado')).toBeVisible();
    await expect(page.getByRole('table').getByText('Anexos')).toBeVisible();
    // El breadcrumb es la salida: sin él no habría vuelta desde el archivo.
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Archivados');
  });

  test('restoring a document reports the container folder that came back with it', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'documents/2/unarchive/' && method === 'PATCH') {
        return json({
          ...archivedDocuments[0],
          is_archived: false,
          archived_at: null,
          restored_chain: [{ id: 9, name: 'Contratos 2024' }],
          moved_to_root: false,
        });
      }
      return baseRoutes({ apiPath, url: route.request().url() });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await page.getByRole('row', { name: /Acta de cierre/i })
      .locator('button[title="Acciones"]').click();
    await sheetAction(page, /^Restaurar/).click();

    await expect(page.getByText('Documento restaurado')).toBeVisible();
    await expect(
      page.getByText(/Se restauró también «Contratos 2024» para que tenga dónde volver/),
    ).toBeVisible();
  });

  test('the state filter starts on active and can widen to both states', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let mixedRequested = false;
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('scope=all')) mixedRequested = true;
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await expect(page.getByRole('table').getByText('Acta de cierre')).toHaveCount(0);

    await page.getByTestId('doc-state-all').click();

    await expect.poll(() => mixedRequested).toBe(true);
    const archivedRow = page.getByRole('row', { name: /Acta de cierre/i });
    await expect(archivedRow).toBeVisible();
    // En una lista mixta cada fila declara su estado.
    await expect(archivedRow.getByTestId('doc-archived-badge')).toBeVisible();
    await expect(page.getByRole('row', { name: /Contrato de Servicios/i })
      .getByTestId('doc-archived-badge')).toHaveCount(0);
  });

  test('searching reaches archived documents from the active view', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('search=')) return json(archivedDocuments);
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await expect(page.getByRole('table').getByText('Contrato de Servicios')).toBeVisible();

    await page.getByRole('searchbox').fill('acta');

    const hit = page.getByRole('row', { name: /Acta de cierre/i });
    await expect(hit).toBeVisible();
    await expect(hit.getByTestId('doc-archived-badge')).toBeVisible();
    // El control se mueve a la vista: la búsqueda ensancha el eje y no debe
    // quedar un filtro en pantalla diciendo lo contrario.
    await expect(page.getByText(/Buscando «acta» en todo el gestor/)).toBeVisible();
  });

  test('an active folder flags the archived items it still holds', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let scopedRequest = null;
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('folder=5')) {
        scopedRequest = url;
        return json(archivedDocuments);
      }
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    const row = page.getByRole('listitem').filter({ hasText: 'temp' });
    const badge = row.getByTestId('folder-archived-badge');

    await expect(badge).toHaveText(/2/);
    await badge.click();

    await expect.poll(() => scopedRequest).toContain('scope=archived');
    await expect(page.getByRole('table').getByText('Acta de cierre')).toBeVisible();
  });

  test('the sidebar counters recompute after archiving, with no reload', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let archived = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/1/archive/' && method === 'PATCH') {
        archived = true;
        return json({ ...activeDocuments[0], is_archived: true });
      }
      if (apiPath === 'documents/counts/' && archived) {
        return json({
          documents: { active: 0, archived: 2, unfiled_active: 0, unfiled_archived: 1 },
          folders: counts.folders,
        });
      }
      if (apiPath === 'documents/' && url.includes('scope=active') && archived) return json([]);
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    const sidebar = page.getByRole('list').filter({ hasText: 'Archivados' });
    await expect(sidebar.getByRole('button', { name: /^Todos/ })).toContainText('1');

    await page.getByRole('row', { name: /Contrato de Servicios/i })
      .locator('button[title="Acciones"]').click();
    await sheetAction(page, /^Archivar/).click();

    await expect(sidebar.getByRole('button', { name: /^Todos/ })).toContainText('0');
    await expect(page.getByTestId('folder-archived-entry')).toContainText('2');
  });

  test('the Archivados view lists archived items with their archive date', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    let archivedRequested = false;
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('scope=archived')) archivedRequested = true;
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
      if (apiPath === 'documents/' && url.includes('scope=archived') && restored) return json([]);
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
