/** R-documents-01: drawer/table and the state catalog must remain reachable from panel navigation. */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

const listScenario = getResponsiveScenario('frontend/pages/panel/documents/index.vue');
const statusesScenario = getResponsiveScenario('frontend/pages/panel/documents/statuses.vue');
const document = { id: 501, title: 'Informe responsivo de agosto', status: 'published', client_name: 'Cliente Atlas Internacional', created_at: '2026-08-20T10:00:00Z', active_states: [] };
const folder = { id: 31, name: 'Futuros Requerimientos Internacionales', slug: 'futuros-requerimientos-internacionales', parent: null, order: 0, is_archived: false, document_count: 1, active_document_count: 1, archived_document_count: 0, children_count: 0, active_children_count: 0, archived_children_count: 0 };
// Full archive-state shape mirrors the archive-flow fixture: the responsive
// special exercises the real mixed active/archived navigation, not an empty mode.
const archiveDocument = { id: 2, title: 'Acta de cierre', status: 'draft', client_name: 'Vieja SAS', created_at: '2025-01-10T10:00:00Z', is_archived: true, archived_at: '2025-02-01T10:00:00Z', archived_cause: 'manual', tag_details: [] };
const archiveFolders = [
  { id: 4, name: 'Contratos', parent: null, order: 0, document_count: 3, children_count: 0, active_document_count: 3, active_children_count: 0, archived_document_count: 0, archived_children_count: 0, is_archived: false },
  { id: 5, name: 'temp', parent: null, order: 1, document_count: 0, children_count: 0, active_document_count: 0, active_children_count: 0, archived_document_count: 2, archived_children_count: 0, is_archived: false },
  { id: 9, name: 'Contratos 2024', parent: null, order: 0, document_count: 5, children_count: 1, active_document_count: 0, active_children_count: 0, archived_document_count: 5, archived_children_count: 1, is_archived: true, archived_at: '2025-02-01T10:00:00Z', archived_cause: 'manual' },
  { id: 10, name: 'Anexos', parent: 9, order: 0, document_count: 1, children_count: 0, active_document_count: 0, active_children_count: 0, archived_document_count: 1, archived_children_count: 0, is_archived: true, archived_at: '2025-02-01T10:00:00Z', archived_cause: 'folder' },
];

async function setupDocuments(page) {
  await setAuthLocalStorage(page, { token: 'documents-token', userAuth: { id: 9001, role: 'admin', is_staff: true, is_superuser: true } });
  await mockApi(page, async ({ apiPath, route }) => {
    const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true, is_superuser: true } });
    if (apiPath === 'documents/') return json(route.request().url().includes('scope=archived') ? [archiveDocument] : [document]);
    if (apiPath === 'documents/counts/') return json({ documents: { active: 1, archived: 1, unfiled_active: 1, unfiled_archived: 0 }, folders: { active: 2, archived: 2 } });
    if (apiPath === 'documents/navigation/') return json({ totals: { active: { folders: 2, documents: 1 }, archived: { folders: 2, documents: 1 } }, unassigned: { project: { active: { folders: 2, documents: 1 }, archived: { folders: 2, documents: 1 } }, client: { active: { folders: 2, documents: 1 }, archived: { folders: 2, documents: 1 } } }, projects: [], clients: [] });
    if (apiPath === 'accounts/panel-preferences/documents/') return json({ navigation_mode: 'project' });
    if (apiPath === 'document-folders/') return json([...archiveFolders, folder]);
    if (apiPath === 'document-tags/' || apiPath === 'document-states/' || apiPath === 'document-state-groups/' || apiPath.startsWith('accounts/saved-filter-tabs')) return json([]);
    if (apiPath.startsWith('accounting/projects/')) return json({ results: [] });
    return null;
  });
}

const documentEntryByProfile = Object.freeze({
  compact: async (page) => { await page.getByRole('button', { name: 'Abrir menú' }).click(); await page.getByRole('link', { name: 'Gestor Documental', exact: true }).click(); },
  portrait: async (page) => { await page.getByRole('button', { name: 'Abrir menú' }).click(); await page.getByRole('link', { name: 'Gestor Documental', exact: true }).click(); },
  landscape: (page) => page.getByRole('link', { name: 'Gestor Documental', exact: true }).click(),
  desktop: (page) => page.getByRole('link', { name: 'Gestor Documental', exact: true }).click(),
  wide: (page) => page.getByRole('link', { name: 'Gestor Documental', exact: true }).click(),
});

async function exerciseFolderDrawer(page) {
  const drawer = page.getByTestId('folder-drawer');
  await page.getByTestId('folder-drawer-trigger').click();
  await expect(drawer).toContainText('Futuros Requerimientos Internacionales');
  await drawer.getByRole('button', { name: 'Cerrar', exact: true }).click();
  await expect(drawer).toHaveCount(0);
}

const folderControlByProfile = Object.freeze({
  compact: exerciseFolderDrawer,
  portrait: exerciseFolderDrawer,
  landscape: (page) => expect(page.getByTestId('folder-panel')).toContainText('Futuros Requerimientos Internacionales'),
  desktop: (page) => expect(page.getByTestId('folder-panel')).toContainText('Futuros Requerimientos Internacionales'),
  wide: (page) => expect(page.getByTestId('folder-panel')).toContainText('Futuros Requerimientos Internacionales'),
});

async function enterDocuments(page, profile) {
  await page.goto('/en-us/panel', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/\/en-us\/panel$/);
  await documentEntryByProfile[profile](page);
  await expect(page).toHaveURL(/\/panel\/documents(?:\?.*)?$/);
  await expect(page.getByRole('heading', { name: 'Gestor Documental', exact: true })).toHaveText('Gestor Documental');
}

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`documents catalog · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));
    test('document list opens its adaptive folder control', {
      tag: ['@flow:admin-document-list', '@outcome:display', '@responsive:documents', `@responsive-scenario:${listScenario.catalogKey}`, `@responsive-batch:${batchForScenario(listScenario.catalogKey)}`, `@viewport:${profile}`],
    }, async ({ page }, testInfo) => {
      await setupDocuments(page);
      // quality: allow-deep-link (the authenticated panel home is the canonical shell entry; this test then reaches Documents through the visible responsive navigation)
      await enterDocuments(page, profile);
      await expect(page.getByText('Informe responsivo de agosto', { exact: true })).toHaveText('Informe responsivo de agosto');
      await folderControlByProfile[profile](page);
      const documentActions = page
        .getByTestId(/^document-(?:row|card)-501$/)
        .filter({ visible: true })
        .getByRole('button', { name: 'Acciones de Informe responsivo de agosto', exact: true });
      await documentActions.click();
      await expect(page.getByTestId('document-actions-list')).toContainText('Editar contenido');
      await page.getByRole('button', { name: 'Cerrar acciones del documento', exact: true }).click();
      await assertResponsiveScenario(page, testInfo, listScenario, { profile });
    });

    test('state catalog is reached from the documents state control', {
      tag: ['@flow:admin-document-list', '@outcome:display', '@responsive:documents', `@responsive-scenario:${statusesScenario.catalogKey}`, `@responsive-batch:${batchForScenario(statusesScenario.catalogKey)}`, `@viewport:${profile}`],
    }, async ({ page }, testInfo) => {
      await setupDocuments(page);
      // quality: allow-deep-link (the authenticated panel home is the canonical shell entry; this test then reaches the state catalog through two visible navigation actions)
      await enterDocuments(page, profile);
      await page.getByTestId('document-state-catalog-link').click();
      await expect(page).toHaveURL(/\/panel\/documents\/statuses$/);
      await expect(page.getByText('Estados de documentos', { exact: true })).toHaveText('Estados de documentos');
      await assertResponsiveScenario(page, testInfo, statusesScenario, { profile });
    });
  });
}

test.describe('documents responsive special', () => {
  test.use(viewportUse('portrait'));
  test('archived mode keeps the active row action reachable after its mixed-state switch', {
    tag: ['@flow:admin-document-archive', '@outcome:display', '@responsive-special:documents', '@viewport:portrait', '@responsive-batch:documents-special-1'],
  }, async ({ page }) => {
    await setupDocuments(page);
    // quality: allow-deep-link (the catalog scenario covers panel entry; this isolates the mixed archive switch and row action)
    await page.goto('/en-us/panel/documents', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Gestor Documental', exact: true })).toHaveText('Gestor Documental');
    // Regression: a narrow folder drawer used to hide the archive switch or
    // leave row actions behind the active-only list.
    const actions = page
      .getByTestId('document-card-501')
      .getByRole('button', { name: 'Acciones de Informe responsivo de agosto', exact: true });
    await actions.click();
    await expect(page.getByTestId('document-actions-list').getByRole('button', { name: /Editar contenido/i })).toHaveText(/Editar contenido/i);
    await page.getByRole('button', { name: 'Cerrar acciones del documento', exact: true }).click();
    await page.getByTestId('folder-drawer-trigger').click();
    await page.getByTestId('folder-drawer').getByTestId('folder-archived-entry').click();
    await expect(page.getByTestId('doc-scope-banner')).toContainText('Modo archivado');
    await expect(page.getByText('Acta de cierre', { exact: true })).toHaveText('Acta de cierre');
  });
});
