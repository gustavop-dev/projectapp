/**
 * Folder-independent document histories in the internal panel.
 *
 * @flow:admin-document-thread
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { viewportUse } from '../helpers/viewports.js';
import { ADMIN_DOCUMENT_THREAD } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const json = (body, status = 200) => ({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

const SOURCE = {
  id: 1,
  title: 'Acta de inicio',
  status: 'published',
  issue_date: '2026-08-20',
  created_at: '2026-08-20T15:00:00Z',
  updated_at: '2026-08-20T15:00:00Z',
  content_markdown: '# Acta de inicio',
  folder: 10,
  folder_name: 'Contratos',
  client_name: 'Cliente Atlas',
  client_display_name: 'Cliente Atlas',
  project: 20,
  project_name: 'Proyecto Atlas',
  is_archived: false,
  tag_details: [],
  active_states: [],
  thread_summary: null,
};

const RELATED = {
  id: 2,
  title: 'Aprobación final',
  status: 'published',
  issue_date: '2026-08-05',
  created_at: '2026-08-05T13:00:00Z',
  is_archived: true,
  archived_at: '2026-08-30T13:00:00Z',
  folder: { id: 11, name: 'Entregas' },
  client: { id: 30, name: 'Cliente Boreal' },
  project: { id: 40, name: 'Proyecto Boreal' },
  default_occurred_on: '2026-08-05',
  available: true,
  unavailable_reason: null,
  thread_summary: null,
};

const THREAD = {
  id: 90,
  title: 'Historia de aprobación',
  document_count: 2,
  items: [
    { id: 901, document: RELATED, occurred_on: '2026-08-05', position: 1 },
    {
      id: 900,
      document: {
        ...SOURCE,
        folder: { id: 10, name: 'Contratos' },
        client: { id: 12, name: 'Cliente Atlas' },
        project: { id: 20, name: 'Proyecto Atlas' },
      },
      occurred_on: '2026-08-20',
      position: 0,
    },
  ],
};

const NAVIGATION = {
  totals: {
    active: { folders: 0, documents: 1 },
    archived: { folders: 0, documents: 0 },
  },
  unassigned: {
    project: { active: { folders: 0, documents: 0 }, archived: { folders: 0, documents: 0 } },
    client: { active: { folders: 0, documents: 0 }, archived: { folders: 0, documents: 0 } },
  },
  projects: [],
  clients: [],
};

async function setupApi(page, options = {}) {
  const state = {
    thread: options.thread ?? null,
    threadStatus: options.threadStatus ?? 200,
    createStatus: options.createStatus ?? 201,
    createBody: null,
  };
  await mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true } });
    if (apiPath === 'accounts/panel-preferences/documents/') return json({ navigation_mode: 'project' });
    if (apiPath === 'documents/navigation/') return json(NAVIGATION);
    if (apiPath === 'documents/counts/') {
      return json({ documents: { active: 1, archived: 0, unfiled_active: 0, unfiled_archived: 0 }, folders: { active: 0, archived: 0 } });
    }
    if (apiPath === 'documents/') {
      const summary = state.thread ? { id: 90, title: state.thread.title, document_count: 2 } : null;
      return json([{ ...SOURCE, thread_summary: summary }]);
    }
    if (apiPath === 'document-folders/' || apiPath === 'document-tags/') return json([]);
    if (apiPath === 'document-states/' || apiPath === 'document-state-groups/') return json([]);
    if (apiPath.startsWith('accounting/projects/')) return json({ results: [] });
    if (apiPath === 'documents/1/thread/') {
      if (state.threadStatus !== 200) return json({ error: 'No se pudo consultar el hilo.' }, state.threadStatus);
      return json(state.thread);
    }
    if (apiPath === 'documents/1/detail/') {
      const summary = state.thread ? { id: 90, title: state.thread.title, document_count: 2 } : null;
      return json({ ...SOURCE, thread_summary: summary });
    }
    if (apiPath === 'documents/2/detail/') return json({ ...RELATED, content_markdown: '# Aprobación' });
    if (apiPath === 'document-threads/candidates/') {
      const includeArchived = new URL(route.request().url()).searchParams.get('scope') === 'all';
      const results = includeArchived ? [RELATED] : [];
      return json({ count: results.length, next: null, previous: null, results });
    }
    if (apiPath === 'document-threads/' && method === 'POST') {
      state.createBody = route.request().postDataJSON();
      if (state.createStatus !== 201) {
        return json({ error: 'El documento ya pertenece a otro hilo.', code: 'document_already_threaded' }, state.createStatus);
      }
      state.thread = THREAD;
      return json(THREAD, 201);
    }
    return null;
  });
  return state;
}

async function openThreadModal(page) {
  await page.goto('/panel/documents', { waitUntil: 'domcontentloaded' });
  await expect(page.getByRole('heading', { name: 'Gestor Documental', exact: true }))
    .toBeVisible({ timeout: 35_000 });
  await page.getByRole('button', { name: 'Acciones de Acta de inicio' }).click();
  await page.getByTestId('document-actions-list')
    .getByRole('button', { name: /Hilo de documentos/ }).click();
  await expect(page.getByTestId('document-thread-content')).toBeVisible();
}

async function openThreadModalFromEditor(page) {
  await page.goto('/panel/documents/1/edit', { waitUntil: 'domcontentloaded' });
  await expect(page.getByTestId('doc-thread-action')).toBeVisible({ timeout: 35_000 });
  await page.getByTestId('doc-thread-action').click();
  await expect(page.getByTestId('document-thread-content')).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await setAuthLocalStorage(page, {
    token: 'document-thread-token',
    userAuth: { id: 8702, role: 'admin', is_staff: true },
  });
});

test.describe('Admin document thread', () => {
  test.describe.configure({ mode: 'serial' });

  test('renders a cross-scope chronology with archived context', {
    tag: [...ADMIN_DOCUMENT_THREAD, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupApi(page, { thread: THREAD });
    // quality: allow-deep-link (the documents route is setup; the modal opens through its visible row action)
    await openThreadModal(page);

    const timeline = page.getByTestId('document-thread-timeline');
    await expect(page.getByTestId('document-thread-title'))
      .toHaveText('Historia de aprobación');
    await expect(timeline.getByTestId('thread-timeline-2')).toContainText('Archivado');
    const titles = await timeline.locator('li button span:nth-child(2)').allTextContents();
    expect(titles).toEqual(['Aprobación final', 'Acta de inicio']);
  });

  test('creates a thread from the candidate list', {
    tag: [...ADMIN_DOCUMENT_THREAD, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const state = await setupApi(page);
    await openThreadModal(page);

    await page.getByTestId('document-thread-include-archived').click();
    await page.getByTestId('thread-candidate-2').click();
    await page.getByTestId('document-thread-save').click();

    await expect(page.getByText('Hilo guardado', { exact: true })).toBeVisible();
    expect(state.createBody).toEqual({
      title: 'Acta de inicio',
      items: [
        { document_id: 1, occurred_on: '2026-08-20' },
        { document_id: 2, occurred_on: '2026-08-05' },
      ],
    });
    await expect(page.getByTestId('document-thread-badge-1')).toContainText('Hilo · 2');
  });

  test('opens the current document thread from the editor action', {
    tag: [...ADMIN_DOCUMENT_THREAD, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // This catches the editor mounting an empty workspace or passing no current document.
    await setupApi(page, { thread: THREAD });
    // quality: allow-deep-link (the editor route is setup; the thread opens through its visible action)
    await openThreadModalFromEditor(page);

    await expect(page.getByTestId('document-thread-title')).toHaveText('Historia de aprobación');
    await expect(page.getByTestId('thread-timeline-1')).toContainText('Acta de inicio');
  });

  test('keeps the workspace open after a membership conflict', {
    tag: [...ADMIN_DOCUMENT_THREAD, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await setupApi(page, { createStatus: 409 });
    await openThreadModal(page);

    await page.getByTestId('document-thread-include-archived').click();
    await page.getByTestId('thread-candidate-2').click();
    await page.getByTestId('document-thread-save').click();

    await expect(page.getByText('El documento ya pertenece a otro hilo.')).toBeVisible();
    await expect(page.getByTestId('document-thread-relate')).toBeVisible();
  });

  test('reports an unavailable thread service', {
    tag: [...ADMIN_DOCUMENT_THREAD, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { threadStatus: 503 });
    await openThreadModal(page);

    await expect(page.getByText('No se pudo consultar el hilo.')).toBeVisible();
    await expect(page.getByTestId('document-thread-content')).toBeVisible();
  });
});

for (const viewport of ['compact', 'portrait', 'landscape', 'desktop', 'wide']) {
  test.describe(`Document thread workspace — ${viewport}`, {
    tag: [`@viewport:${viewport}`],
  }, () => {
    test.use(viewportUse(viewport));

    test(`keeps the modal reachable at the ${viewport} viewport`, {
      tag: [...ADMIN_DOCUMENT_THREAD, '@role:admin', '@outcome:display', '@responsive:documents'],
    }, async ({ page }) => {
      // quality: allow-duplicate (the same modal contract is asserted once per canonical viewport)
      await setupApi(page, { thread: THREAD });
      // quality: allow-deep-link (the documents route is setup; the modal opens through its visible row action)
      await openThreadModal(page);

      const box = await page.getByRole('dialog').boundingBox();
      const size = page.viewportSize();
      expect({
        leftEdgeVisible: box.x >= 0,
        topEdgeVisible: box.y >= 0,
        rightEdgeVisible: box.x + box.width <= size.width,
        bottomEdgeVisible: box.y + box.height <= size.height,
      }).toEqual({
        leftEdgeVisible: true,
        topEdgeVisible: true,
        rightEdgeVisible: true,
        bottomEdgeVisible: true,
      });
    });
  });
}
