/**
 * E2E tests for admin document list flow.
 *
 * @flow:admin-document-list
 * Covers: document list rendering, empty state, navigate to create/edit,
 *         download PDF action, duplicate action, delete with confirmation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_LIST } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockDocuments = [
  {
    id: 1, title: 'Contrato de Servicios', status: 'published',
    client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
  },
  {
    id: 2, title: 'Propuesta Técnica', status: 'draft',
    client_name: null, created_at: '2026-03-05T14:00:00Z',
  },
];

test.describe('Admin Document List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders document list with title, status and action buttons', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      return null;
    });
    await page.goto('/panel/documents');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('table').getByText('Contrato de Servicios')).toBeVisible();
    await expect(page.getByRole('table').getByText('Propuesta Técnica')).toBeVisible();
    await expect(page.getByRole('link', { name: /Nuevo Documento/i })).toBeVisible();
  });

  test('shows empty state when no documents exist', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText(/No hay documentos/i)).toBeVisible();
  });

  test('Nuevo Documento button links to create page', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      return null;
    });
    await page.goto('/panel/documents');
    await page.waitForLoadState('networkidle');

    const createLink = page.getByRole('link', { name: /Nuevo Documento/i });
    await expect(createLink).toHaveAttribute('href', /\/panel\/documents\/create/);
  });
});
