/**
 * E2E tests for downloading a Document as a branded PDF from the editor.
 *
 * @flow:admin-document-pdf-download
 * @flow:admin-document-pdf-preview
 * Covers: the line that names the pages the PDF will bring reacting to the
 *         cover checkboxes, the download asking which version to build when
 *         there are unsaved changes (guardar y descargar / descargar lo
 *         guardado / seguir editando), and the download going straight through
 *         on a clean form.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_PDF_DOWNLOAD, ADMIN_DOCUMENT_PDF_PREVIEW } from '../helpers/flow-tags.js';

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const authCheck = json({ user: { username: 'admin', is_staff: true } });

const mockDocument = {
  id: 1,
  title: 'Contrato de Servicios',
  status: 'draft',
  content_markdown: '# Contrato\n\nEste es el contenido.',
  client: null,
  client_display_name: '',
  project: null,
  language: 'es',
  template_style: 'professional',
  include_portada: true,
  include_subportada: true,
  include_contraportada: true,
  updated_at: '2026-08-18T10:00:00Z',
};

function baseHandler(extra = () => null) {
  return async (ctx) => {
    const { apiPath } = ctx;
    const fromExtra = await extra(ctx);
    if (fromExtra) return fromExtra;
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/1/detail/') return json(mockDocument);
    if (apiPath === 'accounting/projects/') return json({ results: [] });
    if (apiPath === 'document-folders/') return json([]);
    if (apiPath === 'document-tags/') return json([]);
    if (apiPath.startsWith('accounts/saved-filter-tabs')) return json([]);
    if (apiPath === 'proposals/client-profiles/status-counts/') {
      return json({ all: 0, active: 0, orphans: 0, archived: 0 });
    }
    if (apiPath === 'proposals/client-profiles/') return json([]);
    return null;
  };
}

/** El PDF lo arma el backend; acá sólo interesa QUÉ pidió el navegador. */
function pdfStub(calls) {
  return ({ apiPath, method, route }) => {
    if (apiPath !== 'documents/1/pdf/' || method !== 'GET') return null;
    calls.push(route.request().url());
    return { status: 200, contentType: 'application/pdf', body: '%PDF-1.4 fake' };
  };
}

const pagesLine = (page) => page.getByTestId('doc-included-pages');

/**
 * Abrir el editor y esperar a que el formulario esté montado. El primer test
 * de la corrida paga la compilación en frío de la ruta, y sin este ancla el
 * assert de la línea de páginas se comía ese arranque.
 */
async function openEditor(page) {
  await page.goto('/panel/documents/1/edit');
  await expect(page.getByRole('textbox', { name: /^T[ií]tulo\s*\*?$/i }))
    .toHaveValue('Contrato de Servicios', { timeout: 60_000 });
}
const portadaToggle = (page) => page.getByTestId('doc-cover-portada').getByRole('switch');

test.describe('Admin Document — Descargar PDF', () => {
  test.setTimeout(90_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  // Sin esta línea, saber qué trae el archivo obligaba a descargarlo: es el
  // hueco por el que el defecto pasó desapercibido.
  test('the pages line drops the cover as soon as its checkbox goes off', {
    tag: [...ADMIN_DOCUMENT_PDF_DOWNLOAD, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (el editor se alcanza por URL en todo el spec)
    await mockApi(page, baseHandler());
    await openEditor(page);
    await expect(pagesLine(page)).toContainText('portada · subportada · contenido · contraportada');

    await portadaToggle(page).click();

    await expect(pagesLine(page)).toContainText('subportada · contenido · contraportada');
    await expect(pagesLine(page)).not.toContainText('portada · subportada');
  });

  test('downloading with unsaved covers saves them first, so the file matches', {
    tag: [...ADMIN_DOCUMENT_PDF_DOWNLOAD, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const pdfCalls = [];
    let patched = null;
    // quality: allow-deep-link (el editor se alcanza por URL en todo el spec)
    await mockApi(page, baseHandler(async (ctx) => {
      const { apiPath, method, route } = ctx;
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        patched = route.request().postDataJSON();
        return json({ ...mockDocument, include_portada: false, updated_at: '2026-08-18T11:00:00Z' });
      }
      return pdfStub(pdfCalls)(ctx);
    }));
    await openEditor(page);
    await portadaToggle(page).click();

    await page.getByTestId('doc-document-actions-trigger').click();
    await page.getByRole('menuitem', { name: 'Descargar PDF · Profesional', exact: true }).click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByTestId('doc-unsaved-notice')).toBeHidden();
    expect(patched).toMatchObject({ include_portada: false });
    expect(pdfCalls).toHaveLength(1);
  });

  test('choosing the stored version downloads without saving the pending covers', {
    tag: [...ADMIN_DOCUMENT_PDF_DOWNLOAD, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const pdfCalls = [];
    let patchCalled = false;
    // quality: allow-deep-link (el editor se alcanza por URL en todo el spec)
    await mockApi(page, baseHandler(async (ctx) => {
      if (ctx.apiPath === 'documents/1/update/' && ctx.method === 'PATCH') {
        patchCalled = true;
        return json(mockDocument);
      }
      return pdfStub(pdfCalls)(ctx);
    }));
    await openEditor(page);
    await portadaToggle(page).click();

    await page.getByTestId('doc-document-actions-trigger').click();
    await page.getByRole('menuitem', { name: 'Descargar PDF · Profesional', exact: true }).click();
    await page.getByTestId('confirm-modal-secondary').click();

    expect(patchCalled).toBe(false);
    expect(pdfCalls).toHaveLength(1);
    // Lo pendiente sigue pendiente: se descargó lo guardado a sabiendas.
    await expect(page.getByTestId('doc-unsaved-notice')).toBeVisible();
  });

  test('keeping the editing cancels the download instead of building a stale file', {
    tag: [...ADMIN_DOCUMENT_PDF_DOWNLOAD, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const pdfCalls = [];
    // quality: allow-deep-link (el editor se alcanza por URL en todo el spec)
    await mockApi(page, baseHandler(pdfStub(pdfCalls)));
    await openEditor(page);
    await portadaToggle(page).click();

    await page.getByTestId('doc-document-actions-trigger').click();
    await page.getByRole('menuitem', { name: 'Descargar PDF · Profesional', exact: true }).click();
    await page.getByRole('button', { name: 'Seguir editando' }).click();

    expect(pdfCalls).toEqual([]);
    await expect(pagesLine(page)).toContainText('subportada · contenido · contraportada');
  });

  test('a clean form downloads straight away, con el estilo elegido', {
    tag: [...ADMIN_DOCUMENT_PDF_DOWNLOAD, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const pdfCalls = [];
    // quality: allow-deep-link (el editor se alcanza por URL en todo el spec)
    await mockApi(page, baseHandler(pdfStub(pdfCalls)));
    await openEditor(page);
    await expect(pagesLine(page)).toContainText('portada');

    await page.getByTestId('doc-document-actions-trigger').click();
    await page.getByRole('menuitem', { name: 'Descargar PDF · Amigable', exact: true }).click();

    await expect.poll(() => pdfCalls.length).toBe(1);
    expect(pdfCalls[0]).toContain('template=friendly');
  });

  test('the PDF preview shows the generated file for the saved configuration', {
    tag: [...ADMIN_DOCUMENT_PDF_PREVIEW, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    const pdfCalls = [];
    // quality: allow-deep-link (el editor se alcanza por URL en todo el spec)
    await mockApi(page, baseHandler(pdfStub(pdfCalls)));
    await openEditor(page);

    await page.getByTestId('doc-preview-pdf').click();

    await expect(page.getByTestId('doc-pdf-preview-pages'))
      .toContainText('portada · subportada · contenido · contraportada');
    await expect(page.getByTestId('doc-pdf-preview-frame')).toBeVisible();
    expect(pdfCalls[0]).toContain('inline=1');
  });
});
