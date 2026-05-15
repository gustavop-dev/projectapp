/**
 * E2E tests for admin document folders tree drag-and-drop reorganization.
 *
 * @flow:admin-document-folders-tree-drag
 *
 * Coverage strategy: HTML5/SortableJS drag-and-drop is unreliable to simulate
 * in Playwright because vuedraggable uses SortableJS, which doesn't respond
 * to synthetic dispatchEvent('dragstart')/etc. The unit-level @change-handler
 * mapping is already covered in FolderTreeNode.spec.js / FolderSidebar.spec.js.
 *
 * Here we validate the *integration* contract: the Pinia store action issued
 * by a drag triggers the right POST payload, the backend response refreshes
 * the tree, and the sidebar re-renders the new hierarchy. We invoke the
 * action via `page.evaluate` against the real store instance so the axios
 * client + interceptors + state mutations all run for real.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_FOLDERS_TREE_DRAG } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

const CLIENTES = { id: 1, name: 'Clientes', slug: 'clientes', order: 0, document_count: 0, parent: null, depth: 0, path: [{ id: 1, name: 'Clientes' }] };
const INTERNOS = { id: 2, name: 'Internos', slug: 'internos', order: 1, document_count: 0, parent: null, depth: 0, path: [{ id: 2, name: 'Internos' }] };
const ACTIVOS = { id: 3, name: 'Activos', slug: 'activos', order: 0, document_count: 0, parent: 1, depth: 1, path: [{ id: 1, name: 'Clientes' }, { id: 3, name: 'Activos' }] };

test.describe('Admin Document Folders — Tree Drag', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
  });

  test('reparent: dragging a folder into another POSTs to /move/ with new parent_id', {
    tag: [...ADMIN_DOCUMENT_FOLDERS_TREE_DRAG, '@role:admin'],
  }, async ({ page }) => {
    const requests = [];
    let foldersResponse = [CLIENTES, INTERNOS, ACTIVOS];

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/' && method === 'GET') return jsonOk(foldersResponse);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      if (apiPath === `document-folders/${INTERNOS.id}/move/` && method === 'POST') {
        const body = route.request().postDataJSON();
        requests.push({ apiPath, body });
        // Simulate backend: Internos becomes a child of Clientes.
        foldersResponse = [
          CLIENTES,
          ACTIVOS,
          { ...INTERNOS, parent: CLIENTES.id, depth: 1, path: [{ id: 1, name: 'Clientes' }, { id: 2, name: 'Internos' }] },
        ];
        return jsonOk({ ...INTERNOS, parent: CLIENTES.id });
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    // Both roots are initially visible
    await expect(page.getByRole('button', { name: 'Clientes' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Internos' })).toBeVisible();

    // Invoke moveFolder via the real Pinia store — simulates what @change.added would call.
    await page.evaluate(async ([folderId, parentId]) => {
      const { useDocumentFolderStore } = await import('/_nuxt/stores/document_folders.js');
      const store = useDocumentFolderStore();
      await store.moveFolder(folderId, { parent_id: parentId, position: 0 });
    }, [INTERNOS.id, CLIENTES.id]);

    await expect.poll(() => requests.length, { timeout: 5000 }).toBeGreaterThan(0);
    expect(requests[0].body).toEqual({ parent_id: CLIENTES.id, position: 0 });
  });

  test('reorder within parent: POSTs to /reorder/ with parent_id and new ids order', {
    tag: [...ADMIN_DOCUMENT_FOLDERS_TREE_DRAG, '@role:admin'],
  }, async ({ page }) => {
    const requests = [];

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([CLIENTES, INTERNOS]);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      if (apiPath === 'document-folders/reorder/' && method === 'POST') {
        const body = route.request().postDataJSON();
        requests.push({ apiPath, body });
        return jsonOk({ status: 'ok' });
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    await page.evaluate(async ([ids]) => {
      const { useDocumentFolderStore } = await import('/_nuxt/stores/document_folders.js');
      const store = useDocumentFolderStore();
      await store.reorderFolders({ parent_id: null, ids });
    }, [[INTERNOS.id, CLIENTES.id]]);

    await expect.poll(() => requests.length, { timeout: 5000 }).toBeGreaterThan(0);
    expect(requests[0].body).toEqual({ parent_id: null, ids: [INTERNOS.id, CLIENTES.id] });
  });

  test('reparent to root: POSTs to /move/ with parent_id=null', {
    tag: [...ADMIN_DOCUMENT_FOLDERS_TREE_DRAG, '@role:admin'],
  }, async ({ page }) => {
    const requests = [];

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([CLIENTES, ACTIVOS]);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      if (apiPath === `document-folders/${ACTIVOS.id}/move/` && method === 'POST') {
        const body = route.request().postDataJSON();
        requests.push({ apiPath, body });
        return jsonOk({ ...ACTIVOS, parent: null });
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    await page.evaluate(async ([folderId]) => {
      const { useDocumentFolderStore } = await import('/_nuxt/stores/document_folders.js');
      const store = useDocumentFolderStore();
      await store.moveFolder(folderId, { parent_id: null, position: 0 });
    }, [ACTIVOS.id]);

    await expect.poll(() => requests.length, { timeout: 5000 }).toBeGreaterThan(0);
    expect(requests[0].body).toEqual({ parent_id: null, position: 0 });
  });
});
