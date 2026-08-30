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

const navigationPayload = ({ active = 1, archived = 1 } = {}) => ({
  totals: {
    active: { folders: 2, documents: active },
    archived: { folders: 2, documents: archived },
  },
  unassigned: {
    project: {
      active: { folders: 2, documents: active },
      archived: { folders: 2, documents: archived },
    },
    client: {
      active: { folders: 2, documents: active },
      archived: { folders: 2, documents: archived },
    },
  },
  projects: [],
  clients: [],
});

/** Routes shared by every test. `url` distinguishes the requested scope. */
function baseRoutes({ apiPath, url }) {
  const archivedScope = url.includes('scope=archived');
  const mixedScope = url.includes('scope=all');
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'accounts/panel-preferences/documents/') {
    return json({ navigation_mode: 'project' });
  }
  if (apiPath === 'documents/navigation/') return json(navigationPayload());
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
    .getByRole('button', { name: /^Acciones de / }).click();
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
      .getByRole('button', { name: /^Acciones de / }).click();
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
      .getByRole('button', { name: /^Acciones de / }).click();
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

  test('clicking an archived badge mid-search exits the search into the archived folder', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let lastScopedRequest = null;
    await mockApi(page, async ({ apiPath, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/' && url.includes('search=')) return json(archivedDocuments);
      if (apiPath === 'documents/' && url.includes('folder=5')) {
        lastScopedRequest = url;
        return json(archivedDocuments);
      }
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByRole('searchbox').fill('acta');
    await expect(page.getByText(/Buscando «acta» en todo el gestor/)).toBeVisible();

    // La insignia navega a la carpeta en scope archivado; antes el watcher de
    // la búsqueda restauraba el scope previo y aterrizaba en los activos.
    await page.getByRole('listitem').filter({ hasText: 'temp' })
      .getByTestId('folder-archived-badge').click();

    await expect(page.getByText(/Buscando «acta»/)).toHaveCount(0);
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Archivados');
    await expect(page.getByRole('table').getByText('Acta de cierre')).toBeVisible();
    await expect.poll(() => lastScopedRequest).toContain('scope=archived');
  });

  test('the switch stays on at any depth, and the panel still says where you are', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // Antes regía la «regla de resaltado único»: en ámbito archivado se apagaba
    // toda fila para que sólo brillara la entrada «Archivados». Con el modo
    // declarado por el interruptor eso sobra, y apagar la fila activa dejaba al
    // panel sin decir en qué carpeta estaba parado el usuario.
    await mockApi(page, async ({ apiPath, route }) => (
      baseRoutes({ apiPath, url: route.request().url() })
    ));

    // quality: allow-deep-link (el ámbito archivado no es una ruta propia sino
    // un modo de /panel/documents; el interruptor SÍ se pulsa aquí abajo.)
    await page.goto('/panel/documents');
    const archivedSwitch = page.getByTestId('folder-archived-entry');
    await expect(archivedSwitch).toHaveAttribute('aria-checked', 'false');

    await archivedSwitch.click();
    await expect(archivedSwitch).toHaveAttribute('aria-checked', 'true');

    // Entrar a una carpeta no apaga el modo, y ahora la carpeta SÍ se resalta.
    await page.getByRole('row', { name: /Contratos 2024/i }).click();
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Archivados');
    await expect(archivedSwitch).toHaveAttribute('aria-checked', 'true');
    await expect(page.getByTestId('folder-list')
      .getByRole('button', { name: /^Contratos 2024/ }))
      .toHaveAttribute('aria-current', 'page');
  });

  test('archiving an ancestor folder while inside a child lands the view back at the top', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const childFolder = {
      id: 6, name: 'Anexos activos', parent: 4, order: 0,
      document_count: 0, children_count: 0,
      active_document_count: 0, active_children_count: 0,
      archived_document_count: 0, archived_children_count: 0,
      is_archived: false,
    };
    let archived = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'document-folders/4/archive/' && method === 'PATCH') {
        archived = true;
        return json({
          folder: { ...activeFolders[0], is_archived: true },
          archived_folders: 1,
          archived_documents: 3,
        });
      }
      if (apiPath === 'document-folders/') {
        const list = archived
          ? [
            { ...activeFolders[0], is_archived: true, archived_at: '2026-08-13T10:00:00Z', archived_cause: 'manual' },
            { ...childFolder, is_archived: true, archived_at: '2026-08-13T10:00:00Z', archived_cause: 'folder' },
            activeFolders[1],
            ...archivedFolders,
          ]
          : [...activeFolders, childFolder, ...archivedFolders];
        return json(list);
      }
      if (apiPath === 'documents/' && (url.includes('folder=4') || url.includes('folder=6'))) {
        return json([]);
      }
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    // Meterse dos niveles: Contratos (sidebar) → Anexos activos (fila hija).
    await page.getByRole('listitem').filter({ hasText: 'Contratos' })
      .getByRole('button', { name: /^Contratos/ }).click();
    await page.getByRole('row', { name: /Anexos activos/i }).click();
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Todos');

    // Archivar el ANCESTRO desde el sidebar, parado en la descendiente.
    await page.getByRole('listitem').filter({ hasText: 'Contratos' })
      .getByTestId('folder-archive').click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Carpeta archivada')).toBeVisible();
    // Antes el check era de identidad y la vista quedaba parada en la
    // descendiente fantasma, con un empty state falso bajo un breadcrumb vivo.
    await expect(page.getByText('Esta carpeta está vacía')).toHaveCount(0);
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveCount(0);
    await expect(page.getByRole('table').getByText('Contrato de Servicios')).toBeVisible();
    expect(archived).toBe(true);
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
      if (apiPath === 'documents/navigation/') {
        return json(navigationPayload({
          active: archived ? 0 : 1,
          archived: archived ? 2 : 1,
        }));
      }
      if (apiPath === 'documents/' && url.includes('scope=active') && archived) return json([]);
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    // El inventario global vive en el catálogo, fuera de «Carpetas propias».
    const allDocuments = page.getByTestId('documents-navigation-all');
    await expect(allDocuments.getByLabel('1 documentos')).toBeVisible();

    await page.getByRole('row', { name: /Contrato de Servicios/i })
      .getByRole('button', { name: /^Acciones de / }).click();
    await sheetAction(page, /^Archivar/).click();

    await expect(allDocuments.getByLabel('0 documentos')).toBeVisible();
    // El total de archivados acompaña al interruptor, en la cabecera.
    await expect(page.getByTestId('folder-archived-count')).toHaveText('2');
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
      .getByRole('button', { name: /^Acciones de / }).click();
    await sheetAction(page, /^Restaurar/).click();

    await expect(page.getByText('Documento restaurado')).toBeVisible();
    expect(restored).toBe(true);
  });

  test('the folder and scope survive a reload through the url', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => (
      baseRoutes({ apiPath, url: route.request().url() })
    ));

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await page.getByRole('row', { name: /Contratos 2024/i }).click();
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Archivados');
    // Navegar escribe los dos ejes en la URL (router.replace, sin historial).
    await expect.poll(() => page.url()).toContain('folder=9');
    await expect.poll(() => page.url()).toContain('scope=archived');

    // quality: allow-deep-link (recargar con el query ES la conducta bajo
    // prueba: la URL debe reconstruir carpeta y scope sin volver a Todos.)
    await page.reload();

    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Archivados');
    await expect(page.getByRole('table').getByText('Anexos')).toBeVisible();
  });

  test('restoring the folder you are inside follows it back to the active view', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    let restored = false;
    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'document-folders/9/unarchive/' && method === 'PATCH') {
        restored = true;
        return json({
          folder: { ...archivedFolders[0], is_archived: false, archived_at: null },
          restored_folders: 1,
          restored_documents: 5,
          restored_chain: [],
        });
      }
      if (apiPath === 'document-folders/') {
        const list = restored
          ? [
            ...activeFolders,
            { ...archivedFolders[0], is_archived: false, archived_at: null },
            { ...archivedFolders[1], is_archived: false, archived_at: null },
          ]
          : [...activeFolders, ...archivedFolders];
        return json(list);
      }
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await page.getByRole('row', { name: /Contratos 2024/i }).click();

    // Dentro de la carpeta archivada el aviso ofrece restaurarla COMPLETA —
    // las filas del listado solo restauran a las hijas.
    await expect(page.getByTestId('current-folder-archived-alert')).toBeVisible();
    await page.getByTestId('doc-restore-current-folder').click();

    await expect(page.getByText('Carpeta restaurada')).toBeVisible();
    // La vista "sigue" a la carpeta restaurada: scope activo, misma carpeta.
    await expect(page.getByTestId('folder-breadcrumb-root')).toHaveText('Todos');
    await expect(page.getByTestId('current-folder-archived-alert')).toHaveCount(0);
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
      .getByRole('button', { name: /^Acciones de / }).click();
    await sheetAction(page, /^Archivar/).click();

    // exact: el toast repite casi el mismo texto en título y detalle.
    await expect(page.getByText('No se pudo archivar el documento', { exact: true })).toBeVisible();
  });

  test('restoring one document of an archived folder puts it back in the folder, mode off', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // El caso exacto de la ficha: se archiva una carpeta con dos documentos, se
    // restaura UNO, y el documento se daba por perdido porque la vista seguía
    // en el ámbito archivado sin decirlo. Sólo reaparecía al editar la URL.
    const tempArchived = {
      id: 5, name: 'temp', parent: null, order: 0,
      document_count: 2, children_count: 0,
      active_document_count: 0, active_children_count: 0,
      archived_document_count: 2, archived_children_count: 0,
      is_archived: true, archived_at: '2026-08-01T10:00:00Z', archived_cause: 'manual',
    };
    const tempMixed = {
      ...tempArchived, is_archived: false, archived_at: null, archived_cause: null,
      document_count: 1, active_document_count: 1, archived_document_count: 1,
    };
    const doc = (id, title) => ({
      id, title, status: 'draft', client_name: 'Kore', folder: 5,
      created_at: '2026-07-01T10:00:00Z', is_archived: true,
      archived_at: '2026-08-01T10:00:00Z', archived_cause: 'folder', tag_details: [],
    });
    const [first, second] = [doc(20, 'Corrida_Calculadora_Fase_1.5'), doc(21, 'Otro anexo')];
    let restored = false;

    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/20/unarchive/' && method === 'PATCH') {
        restored = true;
        return json({
          ...first, is_archived: false, archived_at: null,
          restored_chain: [{ id: 5, name: 'temp' }], moved_to_root: false,
        });
      }
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/counts/') return json(counts);
      if (apiPath === 'document-tags/') return json([]);
      if (apiPath === 'document-folders/') return json([restored ? tempMixed : tempArchived]);
      if (apiPath === 'documents/') {
        if (!url.includes('folder=5')) return json([]);
        const archivedScope = url.includes('scope=archived');
        if (!restored) return json(archivedScope ? [first, second] : []);
        // Restaurado uno: el otro sigue archivado, a propósito.
        return json(archivedScope ? [second] : [{ ...first, is_archived: false, archived_at: null }]);
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-archived-entry').click();
    await page.getByRole('row', { name: /temp/i }).click();

    await page.getByRole('row', { name: /Corrida_Calculadora_Fase_1\.5/i })
      .getByRole('button', { name: /^Acciones de / }).click();
    await sheetAction(page, /^Restaurar/).click();
    await expect(page.getByText('Documento restaurado')).toBeVisible();

    // Apagar el modo: se permanece en la MISMA carpeta y el documento está ahí,
    // sin recargar y sin tocar la URL — que además suelta el parámetro.
    await page.getByTestId('folder-archived-entry').click();

    await expect(page.getByRole('table').getByText('Corrida_Calculadora_Fase_1.5')).toBeVisible();
    await expect(page.getByRole('table').getByText('Otro anexo')).toHaveCount(0);
    await expect.poll(() => new URL(page.url()).searchParams.get('scope')).toBeNull();
    await expect.poll(() => new URL(page.url()).searchParams.get('folder')).toBe('5');
  });

  test('the archived mode labels the listing and moves every counter with it', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => (
      baseRoutes({ apiPath, url: route.request().url() })
    ));

    // quality: allow-deep-link (el modo archivado se enciende con el
    // interruptor del panel, que SÍ se pulsa en este mismo test.)
    await page.goto('/panel/documents');
    const sidebar = page.getByTestId('folder-list');
    const unfiled = sidebar.getByRole('button', { name: /^Sin carpeta/ });
    // La fila rotula su inventario después del nombre («Contratos — 3
    // documentos»), así que el guion ancla el nombre exacto: en modo archivado
    // aparece también «Contratos 2024» y un prefijo suelto casaría con las dos.
    const contratos = sidebar.getByRole('button', { name: /^Contratos —/ });

    await expect(page.getByTestId('doc-scope-banner')).toHaveCount(0);
    await expect(unfiled).toContainText('1');
    await expect(contratos).toContainText('3');
    // Una carpeta archivada entera no está en el árbol activo.
    await expect(sidebar.getByText('Contratos 2024')).toHaveCount(0);

    await page.getByTestId('folder-archived-entry').click();

    // El ámbito se declara en la cabecera del listado, no sólo en el control.
    await expect(page.getByTestId('doc-scope-banner')).toContainText('Modo archivado');
    // Y los contadores pasan a contar lo archivado, que es lo que se lista.
    await expect(unfiled).toContainText('0');
    await expect(contratos).toContainText('0');
    // La carpeta archivada deja de aparentar que no existe.
    await expect(sidebar.getByText('Contratos 2024')).toBeVisible();
  });

  test('deleting a document leaves the view in the folder it was in', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // Req 31: el mismo chequeo de navegación que se hizo para archivar, ahora
    // para eliminar — la vista decía estar en Todos y listaba otra cosa.
    const inFolder = [{
      id: 30, title: 'Acta parcial', status: 'draft', client_name: 'ACME Corp',
      folder: 4, created_at: '2026-03-01T10:00:00Z', is_archived: false, tag_details: [],
    }];
    let deleted = false;

    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/30/delete/' && method === 'DELETE') {
        deleted = true;
        return json({});
      }
      if (apiPath === 'documents/' && url.includes('folder=4')) {
        return json(deleted ? [] : inFolder);
      }
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-list').getByRole('button', { name: /^Contratos/ }).click();
    await expect(page.getByRole('table').getByText('Acta parcial')).toBeVisible();

    await page.getByRole('row', { name: /Acta parcial/i })
      .getByRole('button', { name: /^Acciones de / }).click();
    await sheetAction(page, /^Eliminar/).click();
    await page.getByTestId('confirm-type-input').fill('DELETE');
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('Documento eliminado')).toBeVisible();
    // Sigue parado en la carpeta: eliminar no es pedir salir de ella.
    await expect.poll(() => new URL(page.url()).searchParams.get('folder')).toBe('4');
    await expect(page.getByTestId('folder-list')
      .getByRole('button', { name: /^Contratos/ })).toHaveAttribute('aria-current', 'page');
  });

  test('moving a document leaves the view in the folder it was in', {
    tag: [...ADMIN_DOCUMENT_ARCHIVE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const inFolder = [{
      id: 31, title: 'Brief inicial', status: 'draft', client_name: 'ACME Corp',
      folder: 4, created_at: '2026-03-01T10:00:00Z', is_archived: false, tag_details: [],
    }];
    let moved = false;

    await mockApi(page, async ({ apiPath, method, route }) => {
      const url = route.request().url();
      if (apiPath === 'documents/31/update/' && method === 'PATCH') {
        moved = true;
        return json({ ...inFolder[0], folder: 5 });
      }
      if (apiPath === 'documents/' && url.includes('folder=4')) {
        return json(moved ? [] : inFolder);
      }
      return baseRoutes({ apiPath, url });
    });

    await page.goto('/panel/documents');
    await page.getByTestId('folder-list').getByRole('button', { name: /^Contratos/ }).click();
    await page.getByRole('row', { name: /Brief inicial/i })
      .getByRole('button', { name: /^Acciones de / }).click();
    await page.getByRole('button', { name: 'Mover a carpeta' }).click();
    const modal = page.locator('div.z-\\[9990\\]').filter({ hasText: 'Mover documento' });
    await modal.getByRole('button', { name: /^temp/ }).click();

    await expect(page.getByRole('table').getByText('Brief inicial')).toHaveCount(0);
    await expect.poll(() => new URL(page.url()).searchParams.get('folder')).toBe('4');
    await expect(page.getByTestId('folder-list')
      .getByRole('button', { name: /^Contratos/ })).toHaveAttribute('aria-current', 'page');
  });
});
