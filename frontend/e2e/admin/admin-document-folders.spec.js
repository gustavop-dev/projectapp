/**
 * E2E tests for the admin document folders flow.
 *
 * @flow:admin-document-folders
 * Covers: folder sidebar navigation and the filter query params sent to the
 *         backend when switching folders.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_FOLDERS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const FOLDER_CUENTAS = { id: 11, name: 'Cuentas de cobro', slug: 'cuentas-de-cobro', parent: null, order: 0, document_count: 1 };
const FOLDER_CONTRATOS = { id: 12, name: 'Contratos', slug: 'contratos', parent: null, order: 0, document_count: 0 };
const PROJECT_KORE = {
  id: 21,
  name: 'Kore Health',
  slug: 'kore-health',
  parent: null,
  order: 0,
  document_count: 2,
  children_count: 1,
  active_document_count: 2,
  active_children_count: 1,
  folder_kind: 'project',
  managed_project: 41,
  is_project_visible: true,
  managed_project_state: { name: 'Activo', system_key: 'active' },
};
const PROJECT_PAUSED = {
  ...PROJECT_KORE,
  id: 22,
  name: 'Candle',
  slug: 'candle',
  managed_project: 42,
  is_project_visible: false,
  managed_project_state: { name: 'Suspendido', system_key: 'paused' },
};

const DOC_IN_FOLDER = {
  id: 1, title: 'Factura ACME', status: 'published',
  client_name: 'ACME', created_at: '2026-04-01T10:00:00Z',
  folder: FOLDER_CUENTAS.id, folder_name: FOLDER_CUENTAS.name,
};
const DOC_ORPHAN = {
  id: 2, title: 'Borrador sin carpeta', status: 'draft',
  client_name: null, created_at: '2026-04-02T10:00:00Z',
  folder: null, folder_name: null,
};

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

async function openDocuments(page) {
  await page.goto('/panel', { waitUntil: 'domcontentloaded' });
  await page.getByRole('link', { name: 'Gestor Documental', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Gestor Documental', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
}

test.describe('Admin Document Folders', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8701, role: 'admin', is_staff: true },
    });
  });

  test('sidebar filters list by folder id via query param', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    const requestedUrls = [];

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_CUENTAS, FOLDER_CONTRATOS]);
      if (apiPath.startsWith('documents/')) {
        const reqUrl = route.request().url();
        requestedUrls.push(reqUrl);
        const u = new URL(reqUrl);
        const folder = u.searchParams.get('folder');
        if (folder === String(FOLDER_CUENTAS.id)) return jsonOk([DOC_IN_FOLDER]);
        return jsonOk([DOC_IN_FOLDER, DOC_ORPHAN]);
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByRole('button', { name: /^Cuentas de cobro/ })).toBeVisible();
    await expect(page.getByRole('table').getByText('Factura ACME')).toBeVisible();
    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeVisible();

    await page.getByRole('button', { name: /^Cuentas de cobro/ }).click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes(`folder=${FOLDER_CUENTAS.id}`)),
      { timeout: 5000 },
    ).toBe(true);

    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeHidden();
    await expect(page.getByRole('table').getByText('Factura ACME')).toBeVisible();
  });

  test('Sin carpeta entry filters for uncategorized documents', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    const requestedUrls = [];

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_CUENTAS]);
      if (apiPath.startsWith('documents/')) {
        const reqUrl = route.request().url();
        requestedUrls.push(reqUrl);
        const u = new URL(reqUrl);
        if (u.searchParams.get('folder') === 'none') return jsonOk([DOC_ORPHAN]);
        return jsonOk([DOC_IN_FOLDER, DOC_ORPHAN]);
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    // Anclado al inicio: la fila ahora muestra el contador de huérfanos
    // ("Sin carpeta 0"), así que el exact-match dejó de servir; el ancla ^
    // sigue evitando el substring-match con los kebabs "Acciones de <título>".
    await page.getByRole('button', { name: /^Sin carpeta/ }).click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes('folder=none')),
      { timeout: 5000 },
    ).toBe(true);

    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeVisible();
    await expect(page.getByRole('table').getByText('Factura ACME')).toBeHidden();
  });

  test('new folder form pre-selects the active folder as parent', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_CUENTAS]);
      if (apiPath.startsWith('documents/')) {
        const u = new URL(route.request().url());
        if (u.searchParams.get('folder') === String(FOLDER_CUENTAS.id)) return jsonOk([DOC_IN_FOLDER]);
        return jsonOk([DOC_IN_FOLDER, DOC_ORPHAN]);
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    // Pararse dentro de la carpeta antes de abrir el gestor.
    await page.getByRole('button', { name: /^Cuentas de cobro/ }).click();
    await page.getByRole('button', { name: 'Nueva carpeta' }).click();

    const parentSelect = page.locator('label', { hasText: 'Dentro de:' }).locator('select');
    await expect(parentSelect).toBeVisible();

    await expect(parentSelect.locator('option:checked')).toHaveText('Cuentas de cobro');
  });

  test('sidebar separates automatic project roots from manual folders', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') {
        return jsonOk([PROJECT_KORE, FOLDER_CONTRATOS]);
      }
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      return null;
    });

    await openDocuments(page);

    const projects = page.getByTestId('project-folder-section');
    const folders = page.getByTestId('manual-folder-section');
    await expect(projects).toContainText('Kore Health');
    await expect(projects).toContainText('Activo');
    await expect(folders).toContainText('Contratos');
    await expect(projects.getByTestId('folder-edit')).toHaveCount(0);
    await expect(projects.getByTestId('folder-archive')).toHaveCount(0);
    await expect(projects.getByTestId('folder-delete')).toHaveCount(0);
  });

  test('configured project-state filter hides excluded roots by default', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') {
        return jsonOk([PROJECT_KORE, PROJECT_PAUSED]);
      }
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      return null;
    });

    await openDocuments(page);

    const projects = page.getByTestId('project-folder-section');
    await expect(projects).toContainText('Kore Health');
    await expect(projects).not.toContainText('Candle');
    await expect(projects).toContainText('1 fuera del filtro de estados');
  });

  test('Ver todos restores access to projects outside the default filter', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') {
        return jsonOk([PROJECT_KORE, PROJECT_PAUSED]);
      }
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      return null;
    });

    await openDocuments(page);
    await page.getByTestId('project-folders-toggle').click();

    await expect(page.getByTestId('project-folder-section')).toContainText('Candle');
    await expect(page.getByTestId('project-folder-22')).toContainText('Suspendido');
  });

  test('project root remains available as a parent for manual subfolders', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([PROJECT_KORE]);
      if (apiPath.startsWith('documents/')) return jsonOk([]);
      return null;
    });

    await openDocuments(page);
    await page.getByTestId('project-folder-21').click();
    await page.getByRole('button', { name: 'Nueva carpeta' }).click();

    const parentSelect = page.locator('label', { hasText: 'Dentro de:' }).locator('select');
    await expect(parentSelect.locator('option:checked')).toHaveText('Kore Health');
  });
});
