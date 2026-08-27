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

// Uno vinculado de verdad (relación) y uno sólo con el nombre libre heredado:
// las columnas deben distinguirlos.
const associatedDocuments = [
  {
    id: 1, title: 'Entregable Kore', status: 'published',
    client: 7, client_display_name: 'Kore SAS',
    project: 11, project_name: 'Kore - Diseño',
    client_name: 'Kore SAS', created_at: '2026-08-01T10:00:00Z',
  },
  {
    id: 2, title: 'Contrato viejo', status: 'draft',
    client: null, client_display_name: null, project: null, project_name: null,
    client_name: 'ACME Corp', created_at: '2026-08-05T14:00:00Z',
  },
];

test.describe('Admin Document List', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders document list with title, status and action buttons', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');

    await expect(page.getByRole('table').getByText('Contrato de Servicios')).toBeVisible();
    await expect(page.getByRole('table').getByText('Propuesta Técnica')).toBeVisible();
    await expect(page.getByRole('link', { name: /Nuevo Documento/i })).toBeVisible();
  });

  test('renders actions as the leading unlabeled column', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display', '@responsive:documents'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display contract: DOM order, blank label and computed fixed width are the observable outcome)
    // quality: allow-deep-link (the canonical list-entry flow is covered elsewhere; this test isolates the table layout contract)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');

    const actionsHeader = page.getByTestId('documents-column-actions');
    await expect(actionsHeader).toBeVisible({ timeout: 15000 });
    const leadingHeaders = await actionsHeader.evaluate((header) => (
      Array.from(header.parentElement.children).slice(0, 2).map((cell) => ({
        testId: cell.getAttribute('data-testid'),
        label: cell.getAttribute('aria-label'),
        text: cell.textContent.trim(),
      }))
    ));
    expect(leadingHeaders).toEqual([
      { testId: 'documents-column-actions', label: 'Acciones', text: '' },
      { testId: null, label: null, text: 'Título' },
    ]);
    await expect(actionsHeader).toHaveCSS('width', '56px');
  });

  test('shows empty state when no documents exist', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display', '@responsive:documents'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');

    await expect(page.getByText(/No hay documentos/i)).toBeVisible();
  });

  test('Nuevo Documento button links to create page', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');

    const createLink = page.getByRole('link', { name: /Nuevo Documento/i });
    await expect(createLink).toHaveAttribute('href', /\/panel\/documents\/create/);
  });

  test('row actions collapse into a single icon that opens the actions modal', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');

    const row = page.getByRole('row', { name: /Contrato de Servicios/i });
    const actionsButton = row.getByRole('button', { name: /^Acciones de / });
    await expect(actionsButton).toBeVisible({ timeout: 15000 });

    const listUrl = page.url();
    await actionsButton.click();

    await expect(page).toHaveURL(listUrl);
    await expect(page.getByRole('button', { name: /Editar contenido/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Renombrar/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Eliminar/i })).toBeVisible();
  });

  test('edit action from the actions modal navigates to the editor', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(mockDocuments) };
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/documents');

    await page.getByRole('row', { name: /Contrato de Servicios/i }).getByRole('button', { name: /^Acciones de / }).click();
    await page.getByRole('button', { name: /Editar contenido/i }).click();

    await expect(page).toHaveURL(/\/panel\/documents\/1\/edit/);
  });

  test('renders the linked client and project in their own columns', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (same baseline as every list test in this spec)
    // quality: allow-no-interaction (pure render contract: the concrete cell
    // values distinguish a real link from the legacy free-text name)
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') return { status: 200, contentType: 'application/json', body: JSON.stringify(associatedDocuments) };
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'accounting/projects/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [] }) };
      return null;
    });
    await page.goto('/panel/documents');

    await expect(page.getByRole('columnheader', { name: 'Cliente' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Proyecto' })).toBeVisible();
    await expect(page.getByTestId('doc-client-cell-1')).toHaveText('Kore SAS');
    await expect(page.getByTestId('doc-project-cell-1')).toHaveText('Kore - Diseño');
    // El nombre libre heredado se muestra pero no es un vínculo.
    await expect(page.getByTestId('doc-client-cell-2')).toHaveText('ACME Corp');
    await expect(page.getByTestId('doc-project-cell-2')).toHaveText('—');
  });

  test('arriving with client=none narrows to unlinked docs and lights the chip', {
    tag: [...ADMIN_DOCUMENT_LIST, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-deep-link (?client= IS the contract the jumps from
    // /panel/clients use; the subject is honoring it on arrival)
    const clientParams = [];
    const projectParams = [];
    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'documents/') {
        const params = new URL(route.request().url()).searchParams;
        clientParams.push(params.get('client'));
        projectParams.push(params.get('project'));
        return { status: 200, contentType: 'application/json', body: JSON.stringify([associatedDocuments[1]]) };
      }
      if (apiPath === 'document-folders/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'document-tags/') return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      if (apiPath === 'accounting/projects/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [] }) };
      return null;
    });
    await page.goto('/panel/documents?client=none');

    await expect(page.getByTestId('documents-filter-client-none'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByRole('table').getByText('Contrato viejo')).toBeVisible();
    expect(clientParams).toContain('none');
    await expect(page).toHaveURL(/client=none/);

    // Y el otro recorte se apila desde su chip: refetch con project=none y
    // el eje espejado en la URL junto al que ya estaba.
    await page.getByTestId('documents-filter-project-none').click();
    await expect(page).toHaveURL(/client=none/);
    await expect(page).toHaveURL(/project=none/);
    await expect
      .poll(() => projectParams.includes('none'), { timeout: 10_000 })
      .toBe(true);
  });
});
