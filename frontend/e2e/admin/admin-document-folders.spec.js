/**
 * E2E tests for admin document folders/tags flow.
 *
 * @flow:admin-document-folders
 * Covers: folder sidebar navigation, tag filter chips, and filter query params
 *         sent to the backend when switching folders or toggling tags.
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

const FOLDER_CUENTAS = { id: 11, name: 'Cuentas de cobro', slug: 'cuentas-de-cobro', order: 0, document_count: 1 };
const FOLDER_CONTRATOS = { id: 12, name: 'Contratos', slug: 'contratos', order: 0, document_count: 0 };

const TAG_URGENTE = { id: 21, name: 'Urgente', slug: 'urgente', color: 'red' };
const TAG_FIRMADO = { id: 22, name: 'Firmado', slug: 'firmado', color: 'emerald' };

const DOC_IN_FOLDER = {
  id: 1, title: 'Factura ACME', status: 'published',
  client_name: 'ACME', created_at: '2026-04-01T10:00:00Z',
  folder: FOLDER_CUENTAS.id, folder_name: FOLDER_CUENTAS.name,
  tag_details: [TAG_URGENTE],
};
const DOC_ORPHAN = {
  id: 2, title: 'Borrador sin carpeta', status: 'draft',
  client_name: null, created_at: '2026-04-02T10:00:00Z',
  folder: null, folder_name: null,
  tag_details: [TAG_FIRMADO],
};

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

test.describe('Admin Document Folders and Tags', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8701, role: 'admin', is_staff: true },
    });
  });

  test('sidebar filters list by folder id via query param', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin'],
  }, async ({ page }) => {
    const requestedUrls = [];

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_CUENTAS, FOLDER_CONTRATOS]);
      if (apiPath === 'document-tags/') return jsonOk([TAG_FIRMADO, TAG_URGENTE]);
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

    await expect(page.getByRole('button', { name: 'Cuentas de cobro' })).toBeVisible();
    await expect(page.getByRole('table').getByText('Factura ACME')).toBeVisible();
    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeVisible();

    await page.getByRole('button', { name: 'Cuentas de cobro' }).click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes(`folder=${FOLDER_CUENTAS.id}`)),
      { timeout: 5000 },
    ).toBe(true);

    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeHidden();
    await expect(page.getByRole('table').getByText('Factura ACME')).toBeVisible();
  });

  test('tag chip toggle filters list via tags query param', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin'],
  }, async ({ page }) => {
    const requestedUrls = [];

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_CUENTAS]);
      if (apiPath === 'document-tags/') return jsonOk([TAG_FIRMADO, TAG_URGENTE]);
      if (apiPath.startsWith('documents/')) {
        const reqUrl = route.request().url();
        requestedUrls.push(reqUrl);
        const u = new URL(reqUrl);
        const tags = u.searchParams.get('tags');
        if (tags === String(TAG_URGENTE.id)) return jsonOk([DOC_IN_FOLDER]);
        return jsonOk([DOC_IN_FOLDER, DOC_ORPHAN]);
      }
      return null;
    });

    await page.goto('/panel/documents');
    await page.waitForLoadState('domcontentloaded');

    const tagChip = page.locator('[data-testid="doc-tag-filters"]').getByRole('button', { name: /Urgente/i });
    await expect(tagChip).toBeVisible();
    await tagChip.click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes(`tags=${TAG_URGENTE.id}`)),
      { timeout: 5000 },
    ).toBe(true);

    await expect(page.getByRole('table').getByText('Factura ACME')).toBeVisible();
    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeHidden();
  });

  test('Sin carpeta entry filters for uncategorized documents', {
    tag: [...ADMIN_DOCUMENT_FOLDERS, '@role:admin'],
  }, async ({ page }) => {
    const requestedUrls = [];

    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'document-folders/') return jsonOk([FOLDER_CUENTAS]);
      if (apiPath === 'document-tags/') return jsonOk([]);
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

    await page.getByRole('button', { name: 'Sin carpeta' }).click();

    await expect.poll(
      () => requestedUrls.some((u) => u.includes('folder=none')),
      { timeout: 5000 },
    ).toBe(true);

    await expect(page.getByRole('table').getByText('Borrador sin carpeta')).toBeVisible();
    await expect(page.getByRole('table').getByText('Factura ACME')).toBeHidden();
  });
});
