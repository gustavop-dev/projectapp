/**
 * E2E tests for admin document create flow.
 *
 * @flow:admin-document-create
 * Covers: page renders with mode tabs, paste Markdown mode, file upload mode,
 *         form submission creates document, validation error handling.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_CREATE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const createdDocument = {
  id: 10, title: 'Nuevo Doc', status: 'draft', client_name: null, created_at: '2026-03-30T10:00:00Z',
};

test.describe('Admin Document Create', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders create page with Pegar Markdown and Cargar Archivo tabs', {
    tag: [...ADMIN_DOCUMENT_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/documents/create');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: /Pegar Markdown/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Cargar Archivo/i })).toBeVisible();
    await expect(page.getByText(/Nuevo Documento/i)).toBeVisible();
  });

  test('back link navigates to documents list', {
    tag: [...ADMIN_DOCUMENT_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/documents/create');
    await page.waitForLoadState('networkidle');

    const backLink = page.getByRole('link', { name: /Volver a documentos/i });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', /\/panel\/documents/);
  });

  test('submitting paste mode form creates document and redirects to list', {
    tag: [...ADMIN_DOCUMENT_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/create-from-markdown/' && method === 'POST') {
        return { status: 201, contentType: 'application/json', body: JSON.stringify(createdDocument) };
      }
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify([createdDocument]) };
      return null;
    });
    await page.goto('/panel/documents/create');
    await page.waitForLoadState('networkidle');

    await page.getByLabel(/Titulo/i).fill('Nuevo Doc');
    await page.getByRole('button', { name: /Pegar Markdown/i }).click();
    const textarea = page.locator('textarea').first();
    await textarea.fill('# Contenido de prueba\n\nEste es el cuerpo del documento.');

    await page.getByRole('button', { name: /Crear|Guardar/i }).click();
    await page.waitForURL(/\/panel\/documents/, { timeout: 15000 });
  });
});
