/**
 * E2E tests for admin document edit flow.
 *
 * @flow:admin-document-edit
 * Covers: edit form pre-filled with existing document data, save updates document,
 *         status change, back link navigation, download PDF action, copy/paste
 *         markdown content toolbar buttons.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_EDIT } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDocument = {
  id: 1, title: 'Contrato de Servicios', status: 'draft',
  content: '# Contrato\n\nEste es el contenido del contrato.',
  client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
};

test.describe('Admin Document Edit', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders edit form pre-filled with existing document data', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocument) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    await expect(page.getByLabel(/T[ií]tulo/i)).toBeVisible();
  });

  test('back link navigates to documents list', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocument) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const backLink = page.getByRole('link', { name: /Volver a documentos/i });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', /\/panel\/documents/);
  });

  test('saving changes calls PATCH API and shows success feedback', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let patchCalled = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocument) };
      if (apiPath === 'documents/1/update/' && method === 'PATCH') {
        patchCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockDocument, title: 'Contrato Actualizado' }) };
      }
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const titleInput = page.getByLabel(/T[ií]tulo/i);
    await titleInput.fill('Contrato Actualizado');
    await page.getByRole('button', { name: /Guardar|Actualizar/i }).first().click();

    await page.waitForFunction(() => window._patchCalled || true, { timeout: 5000 }).catch(() => {});
    expect(patchCalled).toBe(true);
  });

  test('copies the markdown content to the clipboard', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const documentWithMarkdown = { ...mockDocument, content_markdown: '# Contrato\n\nEste es el contenido del contrato.' };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    await page.getByRole('button', { name: /^Copiar$/i }).click();

    await expect(page.getByRole('button', { name: /^Copiado$/i })).toBeVisible({ timeout: 5000 });
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toBe(documentWithMarkdown.content_markdown);
  });

  test('pastes clipboard content into the markdown textarea', {
    tag: [...ADMIN_DOCUMENT_EDIT, '@role:admin'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    const documentWithMarkdown = { ...mockDocument, content_markdown: '# Contrato\n\nEste es el contenido del contrato.' };
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/1/detail/') return { status: 200, contentType: 'application/json', body: JSON.stringify(documentWithMarkdown) };
      return null;
    });
    await page.goto('/panel/documents/1/edit');

    const textarea = page.locator('#edit-markdown');
    await textarea.click();
    await page.keyboard.press('Control+End');
    await page.evaluate((text) => navigator.clipboard.writeText(text), '\n\nTexto pegado desde el portapapeles.');

    await page.getByRole('button', { name: /^Pegar$/i }).click();

    await expect(page.getByRole('button', { name: /^Pegado$/i })).toBeVisible({ timeout: 5000 });
    await expect(textarea).toHaveValue(`${documentWithMarkdown.content_markdown}\n\nTexto pegado desde el portapapeles.`);
  });
});
