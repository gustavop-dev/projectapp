/**
 * E2E test for dragging a document row onto a sidebar folder — the native
 * HTML5 drag-and-drop organize path (distinct from the modal-based "Mover a
 * carpeta" flow already covered in admin-document-move-folder.spec.js).
 *
 * Covers: dragging a `<tr>` document row onto a FolderSidebar folder entry
 * PATCHes documents/{id}/update/ with folder_id and shows a confirmation toast.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_DRAG_ORGANIZE } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const FOLDER_DISENO = { id: 10, name: 'Diseño', slug: 'diseno', parent: null, order: 0, document_count: 1, children_count: 0 };
const FOLDER_DEV    = { id: 11, name: 'Dev', slug: 'dev', parent: null, order: 1, document_count: 0, children_count: 0 };

const DOC = {
  id: 5, title: 'Brief de Proyecto', status: 'published',
  client_name: 'TechCorp', created_at: '2026-04-01T10:00:00Z',
  folder: FOLDER_DISENO.id, folder_id: FOLDER_DISENO.id, folder_name: FOLDER_DISENO.name,
  tag_details: [],
};

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

/**
 * Native HTML5 DnD simulation: Playwright's locator.dragTo() is unreliable
 * with the custom dataTransfer-based handlers this page wires (@dragstart /
 * @dragover.prevent / @drop.prevent). Same shared-DataTransfer-handle +
 * dispatchEvent technique as admin-clients-drag-reassign.spec.js's
 * `dragRowTo` helper.
 */
async function dragDocToFolder(page, rowLocator, folderLocator) {
  const dataTransfer = await page.evaluateHandle(() => new DataTransfer());
  await rowLocator.dispatchEvent('dragstart', { dataTransfer });
  await folderLocator.dispatchEvent('dragover', { dataTransfer });
  await folderLocator.dispatchEvent('drop', { dataTransfer });
  await rowLocator.dispatchEvent('dragend', { dataTransfer }).catch(() => {});
}

test.describe('Admin Document Drag Organize', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8800, role: 'admin', is_staff: true },
    });
  });

  test('dragging a document row onto a sidebar folder moves it there', {
    // Bug this catches: the native-HTML5-DnD wiring (dataTransfer-based,
    // distinct from the sidebar's own vuedraggable-based folder-reorder)
    // silently not firing the drop handler — this path was never exercised
    // by any test before this one.
    tag: [...ADMIN_DOCUMENT_DRAG_ORGANIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (the interaction IS dragDocToFolder's dispatchEvent(dragstart/dragover/drop) sequence on real DOM elements — a genuine native-HTML5-DnD drive, the gate's click/fill/press pattern list just doesn't recognize dispatchEvent)
    let patchBody = null;

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/' && method === 'GET') return jsonOk([DOC]);
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_DISENO, FOLDER_DEV]);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath === `documents/${DOC.id}/update/` && method === 'PATCH') {
        patchBody = route.request().postDataJSON();
        return jsonOk({ ...DOC, ...patchBody });
      }
      return null;
    });

    await page.goto('/panel/documents');
    await expect(page.getByText('Brief de Proyecto').first()).toBeVisible({ timeout: 15000 });

    const row = page.getByRole('row', { name: /Brief de Proyecto/i });
    // Two complementary landmarks exist (the panel nav aside + FolderSidebar) —
    // scope to the one with "Carpetas". The folder button's accessible name is
    // "Dev 0" (name + document-count badge concatenated), so match by prefix.
    const devFolder = page.getByRole('complementary').filter({ hasText: 'Carpetas' })
      .getByRole('button', { name: /^Dev\b/ });
    await expect(devFolder).toBeVisible();

    await dragDocToFolder(page, row, devFolder);

    await expect(() => expect(patchBody).not.toBeNull()).toPass({ timeout: 5000 });
    expect(patchBody.folder_id).toBe(FOLDER_DEV.id);
    await expect(page.getByText('Documento movido a "Dev"')).toBeVisible({ timeout: 10000 });
  });
});
