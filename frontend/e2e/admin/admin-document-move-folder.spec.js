/**
 * E2E tests for admin document move-folder flow.
 *
 * Covers: MoveFolderModal renders folder list; selecting a folder PATCHes
 * documents/{id}/update/ with folder_id; "Sin carpeta" PATCHes with null.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_MOVE_FOLDER } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const FOLDER_DISENO = { id: 10, name: 'Diseño', slug: 'diseno', order: 0, document_count: 1 };
const FOLDER_DEV    = { id: 11, name: 'Dev', slug: 'dev', order: 1, document_count: 0 };

const DOC = {
  id: 5, title: 'Brief de Proyecto', status: 'published',
  client_name: 'TechCorp', created_at: '2026-04-01T10:00:00Z',
  folder: FOLDER_DISENO.id, folder_id: FOLDER_DISENO.id, folder_name: FOLDER_DISENO.name,
  tag_details: [],
};

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

test.describe('Admin Document Move Folder', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8800, role: 'admin', is_staff: true },
    });
  });

  test('move modal renders folder list with Sin carpeta option', {
    tag: [...ADMIN_DOCUMENT_MOVE_FOLDER, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return jsonOk([DOC]);
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_DISENO, FOLDER_DEV]);
      if (apiPath === 'document-tags/') return jsonOk([]);
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Brief de Proyecto').first()).toBeVisible({ timeout: 15000 });

    await page.getByTitle('Mover a carpeta').first().click();

    const modal = page.locator('div.z-\\[9990\\]').filter({ hasText: 'Mover documento' });
    await expect(modal).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Sin carpeta' })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Diseño' })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Dev' })).toBeVisible();
  });

  test('selecting a folder PATCHes documents/{id}/update/ with folder_id', {
    tag: [...ADMIN_DOCUMENT_MOVE_FOLDER, '@role:admin'],
  }, async ({ page }) => {
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
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Brief de Proyecto').first()).toBeVisible({ timeout: 15000 });

    await page.getByTitle('Mover a carpeta').first().click();
    const modal = page.locator('div.z-\\[9990\\]').filter({ hasText: 'Mover documento' });
    await expect(modal).toBeVisible();

    await modal.getByRole('button', { name: 'Dev' }).click();

    await expect(() => expect(patchBody).not.toBeNull()).toPass({ timeout: 5000 });
    expect(patchBody.folder_id).toBe(FOLDER_DEV.id);
  });

  test('"Sin carpeta" PATCHes documents/{id}/update/ with folder_id null', {
    tag: [...ADMIN_DOCUMENT_MOVE_FOLDER, '@role:admin'],
  }, async ({ page }) => {
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
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Brief de Proyecto').first()).toBeVisible({ timeout: 15000 });

    await page.getByTitle('Mover a carpeta').first().click();
    const modal = page.locator('div.z-\\[9990\\]').filter({ hasText: 'Mover documento' });
    await expect(modal).toBeVisible();

    await modal.getByRole('button', { name: 'Sin carpeta' }).click();

    await expect(() => expect(patchBody).not.toBeNull()).toPass({ timeout: 5000 });
    expect(patchBody.folder_id).toBeNull();
  });
});
