/**
 * Context-preserving return navigation for the document editor.
 *
 * @flow:admin-document-edit
 * Covers: complete list URL in the editor backlink, browser Back parity,
 *         page/card focus restoration, contextual labels, and safe fallback.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_EDIT } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const json = (body) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

const authCheck = json({ user: { username: 'admin', is_staff: true } });
const folder = {
  id: 7,
  name: 'Contratos',
  slug: 'contratos',
  parent: null,
  order: 0,
  is_archived: true,
  document_count: 13,
  children_count: 0,
  active_document_count: 0,
  active_children_count: 0,
  archived_document_count: 13,
  archived_children_count: 0,
};
const documents = Array.from({ length: 13 }, (_, index) => ({
  id: index + 1,
  title: `Contrato ${String(index + 1).padStart(2, '0')}`,
  status: 'draft',
  content_markdown: '# Contrato',
  client_name: 'ACME',
  created_at: '2026-08-01T10:00:00Z',
  archived_at: '2026-08-20T10:00:00Z',
  is_archived: true,
  folder: folder.id,
  folder_name: folder.name,
  tag_details: [{ id: 3, name: 'Legal', color: 'blue' }],
}));

async function installDocumentApi(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/counts/') {
      return json({
        documents: { active: 0, archived: 13, unfiled_active: 0, unfiled_archived: 0 },
        folders: { active: 0, archived: 1 },
      });
    }
    if (apiPath === 'documents/13/detail/') return json(documents[12]);
    if (apiPath === 'documents/') return json(documents);
    if (apiPath === 'document-folders/') return json([folder]);
    if (apiPath === 'document-tags/') return json([{ id: 3, name: 'Legal', color: 'blue' }]);
    return null;
  });
}

function expectListContext(page, expected) {
  return expect.poll(() => {
    const url = new URL(page.url());
    return Object.fromEntries([...url.searchParams.entries()].filter(([key]) => key in expected));
  }).toEqual(expected);
}

test.describe('Admin Document Return Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8713, role: 'admin', is_staff: true },
    });
    await installDocumentApi(page);
  });

  test('the editor link restores a complete search context', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.goto('/panel/documents?folder=7&scope=archived&tags=3&order=oldest&view=grid');
    await page.waitForLoadState('domcontentloaded');
    await page.getByRole('searchbox').fill('Contrato');
    await page.getByRole('button', { name: 'Página siguiente' }).click();
    await expect(page.getByTestId('document-card-open-13')).toBeVisible();
    await page.getByTestId('document-card-open-13').click();

    const backLink = page.getByRole('link', { name: 'Volver a resultados de «Contrato»' }).first();
    await expect(backLink).toBeVisible();
    await backLink.click();

    await expectListContext(page, {
      folder: '7', scope: 'archived', tags: '3', q: 'Contrato',
      order: 'oldest', view: 'grid', page: '2', focus: '13',
    });
    await expect(page.getByTestId('document-card-open-13')).toBeFocused();
  });

  test('browser Back restores the archived folder page', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.goto('/panel/documents?folder=7&scope=archived&view=grid&page=2');
    await page.waitForLoadState('domcontentloaded');
    await page.getByTestId('document-card-open-13').click();
    await expect(page.getByRole('link', {
      name: 'Volver a «Contratos» (archivados)',
    }).first()).toBeVisible();

    await page.goBack({ waitUntil: 'domcontentloaded' });

    await expectListContext(page, {
      folder: '7', scope: 'archived', view: 'grid', page: '2',
    });
    await expect(page.getByTestId('document-card-open-13')).toBeVisible();
  });

  test('an untrusted origin falls back to Documents', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await page.goto('/panel/documents/13/edit?from=https%3A%2F%2Fevil.example%2Fsteal');

    const backLink = page.getByRole('link', { name: 'Volver a Documentos' }).first();
    // En un worker frío esta ruta grande puede compilar después de `goto`;
    // esperamos la señal de hidratación sin usar networkidle.
    await expect(backLink).toBeVisible({ timeout: 30_000 });
    const href = await backLink.getAttribute('href');
    expect(new URL(href, page.url()).pathname).toMatch(/\/panel\/documents\/?$/);
    await backLink.click();
    await expect(page).toHaveURL(/\/panel\/documents\/?$/);
  });
});
