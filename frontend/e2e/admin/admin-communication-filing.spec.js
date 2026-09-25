// qa: draft-unvalidated (2026-09-25 — Playwright global warmup did not start specs)
/**
 * @flow:admin-communication-folders
 * E2E coverage for filing manual communication threads in nested folders.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function thread(folderId = null, folderName = '') {
  return {
    id: 41,
    title: 'Aprobación de alcance',
    status: 'open',
    client_id: 7,
    client_name: 'Ana Proyecto',
    client_email: 'ana@example.com',
    project_id: 19,
    project_name: 'Portal de clientes',
    thread_kind: 'manual',
    folder_id: folderId,
    folder_name: folderName,
    messages_count: 1,
    draft_count: 0,
    channels: ['email'],
    latest_message: {
      id: 801, direction: 'outgoing', status: 'sent', content: 'Alcance enviado.',
      occurred_at: '2026-09-24T09:00:00Z',
    },
    last_activity_at: '2026-09-24T09:00:00Z',
    closed_at: null,
    created_at: '2026-09-24T08:00:00Z',
    updated_at: '2026-09-24T09:00:00Z',
    messages: [{
      id: 801,
      thread_id: 41,
      channel: 'email', channel_display: 'Correo', direction: 'outgoing', direction_display: 'Saliente',
      status: 'sent', status_display: 'Enviado', subject: 'Alcance', content: 'Alcance enviado.',
      occurred_at: '2026-09-24T09:00:00Z', recorded_at: '2026-09-24T09:00:00Z',
      updated_at: '2026-09-24T09:00:00Z', source: 'manual', reply_to_id: null, has_reply: false,
      documents: [], date_corrections: [], revisions: [], created_by_name: 'Admin', voided_at: null, void_reason: '',
    }],
  };
}

function facets() {
  return {
    total: 1,
    navigation_total: 1,
    without_project_count: 0,
    projects: [{
      id: 19, name: 'Portal de clientes', client_id: 7, client_name: 'Ana Proyecto',
      catalog_bucket: 'active', count: 1, unavailable: false,
    }],
    clients: [{ id: 7, name: 'Ana Proyecto', count: 1, unavailable: false }],
    filters: {
      status: { open: 1 }, channel: { email: 1 }, direction: { outgoing: 1 },
      message_status: { sent: 1 }, reply_status: { unanswered: 1 },
    },
  };
}

async function setupFilingApi(page, { folderFailure = false } = {}) {
  const folders = [
    { id: 10, name: 'Contratos', parent: null, client: 7, project: 19 },
    { id: 12, name: 'Archivo histórico', parent: 10, client: 7, project: 19 },
  ];
  const state = { thread: thread(), nextFolderId: 11 };
  await mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'accounts/panel-preferences/communications/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({
        navigation_mode: 'project', thread_order: 'recent', page_size: 20, default_channel: 'email',
        show_manual_help: false, navigation_width: 288, legacy_import_allowed: false,
      }) };
    }
    if (apiPath === 'accounts/saved-filter-tabs/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    if (apiPath === 'communications/threads/tab-counts/' && method === 'POST') {
      const counts = Object.fromEntries(route.request().postDataJSON().tabs.map(({ id }) => [String(id), 1]));
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ counts }) };
    }
    if (apiPath === 'communications/folders/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(folders) };
    }
    if (apiPath === 'communications/folders/' && method === 'POST') {
      if (folderFailure) {
        return { status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'El servicio de carpetas no está disponible.' }) };
      }
      const payload = route.request().postDataJSON();
      const created = { id: state.nextFolderId++, ...payload };
      folders.push(created);
      return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
    }
    if (apiPath === 'communications/folders/10/' && method === 'DELETE') {
      return {
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'No se puede eliminar una carpeta que contiene hilos.' }),
      };
    }
    if (apiPath === 'communications/folders/10/' && method === 'PATCH') {
      const payload = route.request().postDataJSON();
      const folder = folders.find((item) => item.id === 10);
      Object.assign(folder, payload);
      return { status: 200, contentType: 'application/json', body: JSON.stringify(folder) };
    }
    if (apiPath === 'communications/threads/' && method === 'GET') {
      const selectedFolder = new URL(route.request().url()).searchParams.get('folder');
      const isSelected = !selectedFolder
        || (selectedFolder === 'none' && !state.thread.folder_id)
        || String(state.thread.folder_id) === selectedFolder;
      const listed = { ...state.thread };
      delete listed.messages;
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: isSelected ? [listed] : [], count: isSelected ? 1 : 0, page: 1, num_pages: 1, facets: facets() }),
      };
    }
    if (apiPath === 'communications/threads/41/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(state.thread) };
    }
    if (apiPath === 'communications/threads/41/' && method === 'PATCH') {
      const { folder } = route.request().postDataJSON();
      const destination = folders.find((item) => item.id === Number(folder));
      state.thread = thread(destination?.id || null, destination?.name || '');
      return { status: 200, contentType: 'application/json', body: JSON.stringify(state.thread) };
    }
    if (apiPath === 'communications/threads/41/close/' && method === 'POST') {
      state.thread = { ...state.thread, status: 'closed', closed_at: '2026-09-25T10:00:00Z' };
      return { status: 200, contentType: 'application/json', body: JSON.stringify(state.thread) };
    }
    if (apiPath === 'documents/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  });
}

async function enterCommunicationsFromPanel(page) {
  await page.goto('/en-us/panel', { waitUntil: 'domcontentloaded' });
  const link = page.getByRole('link', { name: 'Hilos con clientes', exact: true });
  await expect(link).toBeVisible({ timeout: 30_000 });
  await link.click();
  await expect(page.getByRole('heading', { name: 'Comunicaciones', exact: true })).toBeVisible();
}

test.describe('Admin communication filing', () => {
  test.describe.configure({ timeout: 60_000 });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token', userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
  });

  test('creates a nested folder and moves a thread into and out of it', {
    tag: ['@flow:admin-communication-folders', '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    // Regression: filing must persist a nested location and allow a thread to return to Unfiled.
    await setupFilingApi(page);
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();

    const panel = page.getByTestId('communication-folder-panel');
    await panel.getByTestId('communication-folder-10').click();
    await panel.getByRole('button', { name: /Nueva carpeta|New folder/ }).click();
    await page.getByTestId('communication-folder-name').fill('Renovaciones');
    await page.getByTestId('communication-folder-save').click();
    await expect(panel.getByTestId('communication-folder-11')).toContainText('Renovaciones');

    await panel.getByTestId('communication-folder-11').click();
    await expect(page).toHaveURL(/folder=11/);
    await expect(panel.getByRole('navigation', { name: /Ubicación|Location/ }))
      .toHaveText(/Contratos.*Renovaciones/);

    await panel.getByRole('button', { name: /Todos|All/, exact: true }).click();
    await page.getByTestId('communication-thread-row-41').click();
    await page.getByTestId('communication-move-folder').click();
    await page.getByTestId('communication-folder-picker').selectOption('11');
    await page.getByTestId('communication-move-save').click();
    await expect(page.getByText('Renovaciones', { exact: true }).first()).toBeVisible();

    await page.getByRole('button', { name: 'Cerrar detalle del hilo' }).click();
    await panel.getByTestId('communication-folder-11').click();
    await expect(page).toHaveURL(/folder=11/);
    await expect(page.getByTestId('communication-thread-row-41')).toContainText('#41');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/folder=11/);
    await expect(page.getByTestId('communication-thread-row-41')).toContainText('Renovaciones');

    await page.getByTestId('communication-thread-row-41').click();
    await page.getByTestId('communication-move-folder').click();
    await page.getByTestId('communication-folder-picker').selectOption('');
    await page.getByTestId('communication-move-save').click();
    await expect(page.getByText(/Sin carpeta|Unfiled/, { exact: true }).first()).toBeVisible();
  });

  test('shows the selected project folder tree after panel navigation', {
    tag: ['@flow:admin-communication-folders', '@outcome:display', '@role:admin'],
  }, async ({ page }) => {
    // Regression: the project context must expose real folder data after navigating from the panel.
    // quality: allow-deep-link (authenticated dashboard setup; this test enters Communications through its panel link)
    await setupFilingApi(page);
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();

    await expect(page.getByTestId('communication-folder-panel').getByTestId('communication-folder-10'))
      .toContainText('Contratos');
    await page.getByTestId('communication-folder-12').click();
    await expect(page.getByRole('navigation', { name: /Ubicación|Location/ }))
      .toHaveText(/Contratos.*Archivo histórico/);
    await page.getByTestId('communication-folder-panel')
      .getByRole('button', { name: /Todos|All/, exact: true }).click();
    await expect(page.getByTestId('communication-thread-row-41')).toContainText('#41');
  });

  test('renames a folder from its inline editor', {
    tag: ['@flow:admin-communication-folders', '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    // Regression: a renamed folder must keep its place in the project tree.
    await setupFilingApi(page);
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();

    const panel = page.getByTestId('communication-folder-panel');
    await panel.getByRole('button', { name: /Editar carpeta: Contratos|Edit folder: Contratos/ }).click();
    await page.getByTestId('communication-folder-name').fill('Acuerdos');
    await page.getByTestId('communication-folder-save').click();

    await expect(panel.getByTestId('communication-folder-10')).toContainText('Acuerdos');
  });

  test('moves a folder below another folder in the same project', {
    tag: ['@flow:admin-communication-folders', '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    // Regression: changing a parent must expose the folder at its new nested location.
    await setupFilingApi(page);
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();

    const panel = page.getByTestId('communication-folder-panel');
    await panel.getByRole('button', { name: /Nueva carpeta|New folder/ }).click();
    await page.getByTestId('communication-folder-name').fill('Legal');
    await page.getByTestId('communication-folder-save').click();
    await panel.getByRole('button', { name: /Editar carpeta: Contratos|Edit folder: Contratos/ }).click();
    await page.getByTestId('communication-folder-parent').selectOption('11');
    await page.getByTestId('communication-folder-save').click();

    await panel.getByTestId('communication-folder-10').click();
    await expect(page.getByRole('navigation', { name: /Ubicación|Location/ }))
      .toHaveText(/Legal.*Contratos/);
  });

  test('keeps a filed thread discoverable after it is closed', {
    tag: ['@flow:admin-communication-folders', '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    // Regression: closing a classified thread must not remove its folder location or hide its history state.
    await setupFilingApi(page);
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();
    await page.getByTestId('communication-thread-row-41').click();
    await page.getByTestId('communication-move-folder').click();
    await page.getByTestId('communication-folder-picker').selectOption('10');
    await page.getByTestId('communication-move-save').click();
    await page.getByTestId('communication-thread-toggle-41').click();

    await expect(page.getByText('Contratos', { exact: true }).first()).toHaveText('Contratos');
    await expect(page.getByText('Este hilo está cerrado. Reábrelo para registrar o editar mensajes.'))
      .toHaveText('Este hilo está cerrado. Reábrelo para registrar o editar mensajes.');
  });

  test('keeps the folder editor open when deletion is rejected for contained threads', {
    tag: ['@flow:admin-communication-folders', '@outcome:error', '@role:admin'],
  }, async ({ page }) => {
    // Regression: a non-empty folder must show the server rejection instead of disappearing from the tree.
    await setupFilingApi(page);
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();

    const panel = page.getByTestId('communication-folder-panel');
    await panel.getByRole('button', { name: /Editar carpeta: Contratos|Edit folder: Contratos/ }).click();
    await page.getByRole('button', { name: /Eliminar carpeta|Delete folder/ }).click();
    await page.getByTestId('communication-folder-save').click();

    await expect(page.getByRole('alert')).toContainText('No se puede eliminar una carpeta que contiene hilos.');
    await expect(page.getByTestId('communication-folder-save')).toHaveText(/Eliminar carpeta|Delete folder/);
  });

  test('keeps the folder form open when saving fails on the server', {
    tag: ['@flow:admin-communication-folders', '@outcome:failure', '@role:admin'],
  }, async ({ page }) => {
    // Regression: an unavailable folder service must preserve the name so the operator can retry.
    await setupFilingApi(page, { folderFailure: true });
    await enterCommunicationsFromPanel(page);
    await page.getByTestId('communications-navigation-project-19').click();

    const panel = page.getByTestId('communication-folder-panel');
    await panel.getByRole('button', { name: /Nueva carpeta|New folder/ }).click();
    const name = page.getByTestId('communication-folder-name');
    await name.fill('Contratos');
    await page.getByTestId('communication-folder-save').click();

    await expect(page.getByRole('alert')).toContainText('El servicio de carpetas no está disponible.');
    await expect(name).toHaveValue('Contratos');
  });
});
