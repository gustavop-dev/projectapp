/**
 * E2E tests for the admin document gallery view.
 *
 * @flow:admin-document-gallery
 * Covers: list/gallery toggle, card rendering with mini-preview data,
 *         persistence across reloads, actions sheet from a card,
 *         switching back to list.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_GALLERY } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const mockDocuments = [
  {
    id: 1, title: 'Contrato de Servicios', status: 'published',
    client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
    content_excerpt: '# Contrato\n\nAlcance del servicio con **términos**.',
    tag_details: [{ id: 1, name: 'Legal', color: 'blue' }],
  },
  {
    id: 2, title: 'Propuesta Técnica', status: 'draft',
    client_name: null, created_at: '2026-03-05T14:00:00Z',
    content_excerpt: '## Stack\n\n- Django\n- Nuxt',
    tag_details: [],
  },
];

async function mockDocumentsApi(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
    }
    if (apiPath === 'document-folders/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === 'document-tags/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

test.describe('Admin Document Gallery', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8700, role: 'admin', is_staff: true },
    });
  });

  test('toggles to gallery view and renders document cards with previews', {
    tag: [...ADMIN_DOCUMENT_GALLERY, '@role:admin'],
  }, async ({ page }) => {
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    // Default is list: the table is visible, the grid is not.
    await expect(page.getByRole('table')).toBeVisible();

    await page.getByTestId('doc-view-grid').click();

    await expect(page.getByRole('table')).toBeHidden();
    const grid = page.getByTestId('documents-grid');
    await expect(grid).toBeVisible();
    await expect(grid.getByText('Contrato de Servicios')).toBeVisible();
    await expect(grid.getByText('Propuesta Técnica')).toBeVisible();
    // Status badges render on the cards.
    await expect(grid.getByText('Publicado')).toBeVisible();
    await expect(grid.getByText('Borrador')).toBeVisible();
    // Mini-preview renders sanitized markdown from content_excerpt.
    await expect(grid.getByText('Alcance del servicio', { exact: false })).toBeVisible();
  });

  test('persists the chosen view across reloads via localStorage', {
    tag: [...ADMIN_DOCUMENT_GALLERY, '@role:admin'],
  }, async ({ page }) => {
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    await page.getByTestId('doc-view-grid').click();
    await expect(page.getByTestId('documents-grid')).toBeVisible();

    await page.reload({ waitUntil: 'domcontentloaded' });

    await expect(page.getByTestId('documents-grid')).toBeVisible();
    await expect(page.getByRole('table')).toBeHidden();

    const stored = await page.evaluate(
      () => window.localStorage.getItem('projectapp-documents-view-mode'),
    );
    expect(stored).toBe(JSON.stringify('grid'));
  });

  test('opens the actions sheet from a card kebab', {
    tag: [...ADMIN_DOCUMENT_GALLERY, '@role:admin'],
  }, async ({ page }) => {
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    await page.getByTestId('doc-view-grid').click();
    await page.getByRole('button', { name: 'Acciones de Contrato de Servicios' }).click();

    await expect(page.getByRole('button', { name: /Descargar PDF/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Duplicar/i })).toBeVisible();
  });

  test('switches back to list view and shows the table again', {
    tag: [...ADMIN_DOCUMENT_GALLERY, '@role:admin'],
  }, async ({ page }) => {
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    await page.getByTestId('doc-view-grid').click();
    await expect(page.getByTestId('documents-grid')).toBeVisible();

    await page.getByTestId('doc-view-list').click();

    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByRole('table').getByText('Contrato de Servicios')).toBeVisible();
  });
});
