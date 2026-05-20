/**
 * E2E tests for the admin document folder hierarchy flow.
 *
 * @flow:admin-document-folder-hierarchy
 * Covers: root-only sidebar, subfolder rows inside the table, and breadcrumb
 *         navigation when entering and leaving nested folders.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_FOLDER_HIERARCHY } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

// Árbol: Raíz A (11) -> Subcarpeta (21) -> Sub-sub (31) ; Raíz B (12)
const FOLDER_ROOT = {
  id: 11, name: 'Raiz A', slug: 'raiz-a', parent: null,
  order: 0, document_count: 1, children_count: 1,
};
const FOLDER_OTHER_ROOT = {
  id: 12, name: 'Raiz B', slug: 'raiz-b', parent: null,
  order: 1, document_count: 0, children_count: 0,
};
const FOLDER_SUB = {
  id: 21, name: 'Subcarpeta Uno', slug: 'subcarpeta-uno', parent: 11,
  order: 0, document_count: 1, children_count: 1,
};
const FOLDER_SUBSUB = {
  id: 31, name: 'Sub Sub', slug: 'sub-sub', parent: 21,
  order: 0, document_count: 0, children_count: 0,
};

const ALL_FOLDERS = [FOLDER_ROOT, FOLDER_OTHER_ROOT, FOLDER_SUB, FOLDER_SUBSUB];

const DOC_IN_ROOT = {
  id: 1, title: 'Doc En Raiz', status: 'published',
  client_name: 'ACME', created_at: '2026-04-01T10:00:00Z',
  folder: FOLDER_ROOT.id, folder_name: FOLDER_ROOT.name, tag_details: [],
};
const DOC_IN_SUB = {
  id: 2, title: 'Doc En Subcarpeta', status: 'draft',
  client_name: null, created_at: '2026-04-02T10:00:00Z',
  folder: FOLDER_SUB.id, folder_name: FOLDER_SUB.name, tag_details: [],
};

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

function documentsForFolder(folder) {
  if (folder === String(FOLDER_ROOT.id)) return [DOC_IN_ROOT];
  if (folder === String(FOLDER_SUB.id)) return [DOC_IN_SUB];
  if (folder === String(FOLDER_SUBSUB.id)) return [];
  return [DOC_IN_ROOT, DOC_IN_SUB];
}

test.describe('Admin Document Folder Hierarchy', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8701, role: 'admin', is_staff: true },
    });
  });

  function sidebar(page) {
    return page.locator('aside', {
      has: page.getByRole('heading', { name: 'Carpetas' }),
    });
  }

  test('sidebar shows only root folders', {
    tag: [...ADMIN_DOCUMENT_FOLDER_HIERARCHY, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk(ALL_FOLDERS);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath.startsWith('documents/')) {
        const u = new URL(route.request().url());
        return jsonOk(documentsForFolder(u.searchParams.get('folder')));
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    const bar = sidebar(page);
    await expect(bar.getByRole('button', { name: 'Raiz A' })).toBeVisible();
    await expect(bar.getByRole('button', { name: 'Raiz B' })).toBeVisible();
    // La subcarpeta no debe listarse en el sidebar.
    await expect(bar.getByRole('button', { name: 'Subcarpeta Uno' })).toHaveCount(0);
  });

  test('entering a folder reveals subfolder rows and the breadcrumb', {
    tag: [...ADMIN_DOCUMENT_FOLDER_HIERARCHY, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk(ALL_FOLDERS);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath.startsWith('documents/')) {
        const u = new URL(route.request().url());
        return jsonOk(documentsForFolder(u.searchParams.get('folder')));
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    await sidebar(page).getByRole('button', { name: 'Raiz A' }).click();

    const breadcrumb = page.getByRole('navigation', { name: 'Ruta de carpetas' });
    await expect(breadcrumb).toBeVisible();
    await expect(breadcrumb.getByText('Raiz A')).toBeVisible();

    const table = page.getByRole('table');
    await expect(table.getByText('Subcarpeta Uno')).toBeVisible();
    await expect(table.getByText('Doc En Raiz')).toBeVisible();
  });

  test('navigates into a subfolder and back via the breadcrumb', {
    tag: [...ADMIN_DOCUMENT_FOLDER_HIERARCHY, '@role:admin'],
  }, async ({ page }) => {
    const requestedUrls = [];

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk(ALL_FOLDERS);
      if (apiPath === 'document-tags/') return jsonOk([]);
      if (apiPath.startsWith('documents/')) {
        const reqUrl = route.request().url();
        requestedUrls.push(reqUrl);
        const u = new URL(reqUrl);
        return jsonOk(documentsForFolder(u.searchParams.get('folder')));
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    // Entrar a la carpeta raíz, luego a la subcarpeta desde la tabla.
    await sidebar(page).getByRole('button', { name: 'Raiz A' }).click();
    await page.getByRole('table').getByText('Subcarpeta Uno').click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes(`folder=${FOLDER_SUB.id}`)),
      { timeout: 5000 },
    ).toBe(true);

    const breadcrumb = page.getByRole('navigation', { name: 'Ruta de carpetas' });
    await expect(breadcrumb.getByText('Subcarpeta Uno')).toBeVisible();
    await expect(page.getByRole('table').getByText('Doc En Subcarpeta')).toBeVisible();

    // Volver a la carpeta raíz desde el breadcrumb.
    await breadcrumb.getByRole('button', { name: 'Raiz A' }).click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes(`folder=${FOLDER_ROOT.id}`)),
      { timeout: 5000 },
    ).toBe(true);

    await expect(page.getByRole('table').getByText('Doc En Raiz')).toBeVisible();
  });
});
