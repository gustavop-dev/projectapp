/**
 * E2E tests for the admin document duplicate flow.
 *
 * @flow:admin-document-duplicate
 * Covers: "Duplicar" from the actions sheet firing POST
 *         /api/documents/<id>/duplicate/, the success toast and the copy
 *         appearing in the refreshed list, plus the error branch.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_DUPLICATE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const original = {
  id: 1, title: 'Contrato de Servicios', status: 'published',
  client_name: 'ACME Corp', created_at: '2026-03-01T10:00:00Z',
};
const copy = { ...original, id: 2, title: 'Contrato de Servicios (copia)', status: 'draft' };

function baseRoutes(apiPath, documents) {
  if (apiPath === 'auth/check/') return authCheck;
  if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(documents) };
  if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
  return null;
}

async function openActionsAndDuplicate(page) {
  await page.goto('/panel/documents');
  await page.getByRole('row', { name: /Contrato de Servicios/i }).locator('button[title="Acciones"]').click();
  await page.getByRole('button', { name: /Duplicar/i }).click();
}

test.describe('Admin Document Duplicate', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('duplicating posts to the endpoint and shows the copy in the list', {
    tag: [...ADMIN_DOCUMENT_DUPLICATE, '@role:admin'],
  }, async ({ page }) => {
    const state = { duplicated: false };
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/duplicate/' && method === 'POST') {
        state.duplicated = true;
        return { status: 201, contentType: 'application/json', body: JSON.stringify(copy) };
      }
      return baseRoutes(apiPath, state.duplicated ? [copy, original] : [original]);
    });
    await openActionsAndDuplicate(page);

    await expect(page.getByText('Documento duplicado')).toBeVisible();
    await expect(page.getByRole('table').getByText('Contrato de Servicios (copia)')).toBeVisible();
    expect(state.duplicated).toBe(true);
  });

  test('shows the error toast when the duplicate fails', {
    tag: [...ADMIN_DOCUMENT_DUPLICATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'documents/1/duplicate/' && method === 'POST') {
        return { status: 500, contentType: 'application/json', body: '{}' };
      }
      return baseRoutes(apiPath, [original]);
    });
    await openActionsAndDuplicate(page);

    await expect(page.getByText('No se pudo duplicar el documento', { exact: true })).toBeVisible();
  });
});
