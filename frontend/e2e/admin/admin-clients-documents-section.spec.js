/**
 * FLOW: admin-clients-documents-section
 *
 * La ficha expandible de /panel/clients lista los últimos documentos del
 * cliente (título → editor, proyecto, estado, fecha) y "Ver todos (N)" salta
 * al gestor de documentos ya filtrado por él — el listado de documentos de un
 * cliente se alcanza desde su ficha sin pasar por el filtro.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENTS_DOCUMENTS_SECTION } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({
    user: { username: 'admin', is_staff: true, is_superuser: true },
  }),
};

const CLIENT_ROW = {
  id: 101,
  name: 'Kore Healths',
  email: 'kore@test.com',
  phone: '',
  company: 'Kore',
  is_onboarded: true,
  is_email_placeholder: false,
  total_proposals: 1,
  projects_count: 1,
  diagnostics_count: 0,
  incomes_count: 0,
  hostings_count: 0,
  active_hostings_count: 0,
  active_projects_count: 1,
  documents_count: 7,
  documents_no_project_count: 2,
  last_document_at: '2026-08-10T10:00:00Z',
  is_orphan: false,
  is_inactive: false,
  deactivated_at: null,
  accepted_count: 0,
  last_status: 'sent',
  last_sent_at: '2026-05-01T10:00:00Z',
  project_types: [],
  market_types: [],
  nit: '900123456',
  cedula: '',
  billing_code: 'KORE',
  created_at: '2026-01-01T10:00:00Z',
  updated_at: '2026-08-10T10:00:00Z',
};

const CLIENT_DETAIL = {
  ...CLIENT_ROW,
  proposals: [],
  projects: [],
  diagnostics: [],
  hostings: [],
  hostings_monthly_total: '0',
  incomes: [],
  documents: [
    {
      id: 31, title: 'Entregable agosto', status: 'published',
      project: 11, project_name: 'Kore - Diseño',
      folder_name: 'Kore - Diseño', created_at: '2026-08-10T10:00:00Z',
    },
    {
      id: 30, title: 'Acta de inicio', status: 'draft',
      project: null, project_name: null,
      folder_name: 'Kore - Diseño', created_at: '2026-08-01T10:00:00Z',
    },
  ],
  documents_total: 7,
};

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    if (apiPath === 'proposals/client-profiles/status-counts/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ all: 1, active: 1, orphans: 0, inactive: 0 }),
      };
    }
    if (apiPath === 'proposals/client-profiles/101/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(CLIENT_DETAIL),
      };
    }
    if (apiPath === 'proposals/client-profiles/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([CLIENT_ROW]),
      };
    }
    // Destino del salto "Ver todos": el gestor de documentos completo.
    if (apiPath === 'documents/counts/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: { active: 0, archived: 0, unfiled_active: 0, unfiled_archived: 0 },
          folders: { active: 0, archived: 0 },
        }),
      };
    }
    if (apiPath === 'documents/') {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    if (apiPath === 'document-folders/' || apiPath === 'document-tags/') {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    if (apiPath.startsWith('accounting/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], meta: {} }),
      };
    }
    return null;
  });
}

async function openFicha(page) {
  await page.goto('/panel/clients');
  await expect(page.getByRole('heading', { name: 'Clientes' }))
    .toBeVisible({ timeout: 30_000 });
  await page.getByTestId('client-row-101').click();
}

test.describe('Admin Clients Documents Section', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true, is_superuser: true },
    });
  });

  test('the expanded ficha lists the recent documents with their project', {
    tag: [...ADMIN_CLIENTS_DOCUMENTS_SECTION, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (reaching /panel/clients through the sidebar is
    // its own flow; the subject here is the expanded row's Documentos section)
    await setupMock(page);
    await openFicha(page);

    const linked = page.getByTestId('client-document-row-31');
    await expect(linked).toBeVisible();
    await expect(linked).toContainText('Entregable agosto');
    await expect(linked).toContainText('Kore - Diseño');
    // El título entra al editor del documento.
    await expect(linked.getByRole('link', { name: 'Entregable agosto' }))
      .toHaveAttribute('href', /\/panel\/documents\/31\/edit/);
    // El que quedó a medio asociar muestra el hueco, no lo esconde.
    await expect(page.getByTestId('client-document-row-30')).toContainText('—');
  });

  test('Ver todos opens the documents manager already filtered by the client', {
    tag: [...ADMIN_CLIENTS_DOCUMENTS_SECTION, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupMock(page);
    await openFicha(page);

    const seeAll = page.getByTestId('client-documents-all-101');
    await expect(seeAll).toHaveText(/Ver todos \(7\)/);

    await seeAll.click();

    // 30s: la primera navegación a /panel/documents compila el chunk de la
    // página en dev y puede superar el timeout default del expect.
    await expect(page).toHaveURL(/\/panel\/documents\?client=101/, { timeout: 30_000 });
    await expect(page.getByTestId('doc-association-filters'))
      .toBeVisible({ timeout: 30_000 });
  });
});
