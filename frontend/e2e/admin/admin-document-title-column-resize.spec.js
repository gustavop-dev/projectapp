/**
 * Long-title disclosure and reusable column resizing on /panel/documents.
 *
 * @flow:admin-document-title-column-resize
 * Covers: clipped-only full-name hints, compact in-place disclosure, pointer
 *         resize persistence, fixed workflow/actions tracks and double-click reset.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const WIDTH_KEY = 'projectapp-table-widths:documents-list';
const LONG_TITLE = 'Cliente Atlas — Contrato marco de servicios profesionales para el Comité Ejecutivo Regional — versión final aprobada para firma del 25 de agosto de 2026';
const STATE_GROUPS = [
  { id: 1, name: 'Ciclo', selection_mode: 'exclusive', order: 0, is_active: true },
];
const SENT_STATE = {
  id: 11,
  name: 'Enviado',
  color: 'blue',
  system_key: 'sent',
  group: 1,
  group_id: 1,
  group_name: 'Ciclo',
  group_mode: 'exclusive',
  group_order: 0,
  order: 1,
  is_active: true,
  merged_into: null,
};

const jsonOk = (body) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(body),
});

const authCheck = jsonOk({
  user: { username: 'admin', is_staff: true, is_superuser: true },
});

function documentFixture(id, title) {
  return {
    id,
    title,
    status: 'published',
    is_archived: false,
    folder: null,
    folder_name: '',
    client: 101,
    client_display_name: 'Cliente Atlas Internacional',
    client_name: 'Cliente Atlas Internacional',
    project: 12,
    project_name: 'Proyecto Atlas',
    content_excerpt: 'Resumen operativo del documento.',
    active_states: [{
      id: 101,
      duration_seconds: 86400,
      opened_at: '2026-08-24T10:00:00Z',
      state: SENT_STATE,
    }],
    created_at: '2026-08-25T10:00:00Z',
  };
}

const DOCUMENTS = [
  documentFixture(501, LONG_TITLE),
  documentFixture(502, 'Acta breve'),
];

async function mockDocuments(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/') return jsonOk(DOCUMENTS);
    if (apiPath === 'documents/counts/') {
      return jsonOk({
        documents: { active: 2, archived: 0, unfiled_active: 2, unfiled_archived: 0 },
        folders: { active: 0, archived: 0 },
      });
    }
    if (apiPath === 'document-folders/') return jsonOk([]);
    if (apiPath === 'document-states/') return jsonOk([SENT_STATE]);
    if (apiPath === 'document-state-groups/') return jsonOk(STATE_GROUPS);
    if (apiPath.startsWith('accounting/projects/')) return jsonOk({ results: [] });
    return null;
  });
}

async function openDocuments(page) {
  // quality: allow-deep-link (la navegación del sidebar ya pertenece a los specs de layout)
  await mockDocuments(page);
  await page.goto('/panel/documents', { waitUntil: 'domcontentloaded' });
  await expect(page.getByText(LONG_TITLE, { exact: true }).first()).toBeVisible({ timeout: 30_000 });
  await page.evaluate(async () => {
    await document.fonts.ready;
    window.dispatchEvent(new Event('resize'));
  });
}

async function dragTitleBy(page, delta) {
  const handle = page.getByTestId('documents-title-resize-handle');
  const box = await handle.boundingBox();
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + delta, y, { steps: 5 });
  await page.mouse.up();
}

async function columnWidth(page, name) {
  return page.getByRole('columnheader', { name, exact: true })
    .evaluate((element) => element.getBoundingClientRect().width);
}

test.describe('Admin Document Title Column Resize', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'document-title-column-token',
      userAuth: { id: 9501, role: 'admin', is_staff: true, is_superuser: true },
    });
    await page.addInitScript(() => {
      localStorage.setItem('projectapp-documents-view-mode', 'list');
    });
  });

  test('exposes the full-name hint only for clipped titles', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (la navegación del sidebar pertenece a los flows de layout; este caso aísla la medición de los títulos)
    // quality: allow-no-interaction (es un outcome display que contrasta recorte real contra texto completo; los otros cuatro casos operan los controles)
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const longTitle = page.getByTestId('document-open-501');
    await expect(page.getByTestId('document-open-501-toggle')).toBeVisible();
    await expect(longTitle).toHaveAttribute('title', LONG_TITLE);
    await expect(page.getByTestId('document-open-502-toggle')).toHaveCount(0);
    await expect(page.getByTestId('document-open-502')).not.toHaveAttribute('title', /.+/);
  });

  test('reveals a clipped title in place on the compact gallery', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 835, height: 1195 });
    await openDocuments(page);

    const link = page.getByTestId('document-card-open-501');
    const toggle = page.getByTestId('document-card-open-501-toggle');
    await expect(toggle).toBeVisible();
    await toggle.click();

    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
    await expect(link).not.toHaveAttribute('title', LONG_TITLE);
    await expect(page).toHaveURL(/\/panel\/documents\/?$/);
    const dimensions = await link.evaluate((element) => ({
      client: element.clientHeight,
      scroll: element.scrollHeight,
    }));
    expect(dimensions.scroll - dimensions.client).toBeLessThanOrEqual(1);
  });

  test('restores a dragged title width after reload', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (page.mouse exercises the real pointer-captured separator drag)
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    await dragTitleBy(page, 80);
    const stored = await page.evaluate((key) => JSON.parse(localStorage.getItem(key)), WIDTH_KEY);
    expect(stored.title).toBeGreaterThanOrEqual(395);
    expect(stored.title).toBeLessThanOrEqual(405);

    await page.reload({ waitUntil: 'domcontentloaded' });
    const handle = page.getByTestId('documents-title-resize-handle');
    await expect(handle).toBeVisible({ timeout: 30_000 });
    await expect(handle).toHaveAttribute('aria-valuenow', String(stored.title));
  });

  test('preserves fixed tracks while title grows', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const before = {
      workflow: await columnWidth(page, 'Estados'),
      actions: await columnWidth(page, 'Acciones'),
    };
    const handle = page.getByTestId('documents-title-resize-handle');
    await handle.press('End');
    await expect(handle).toHaveAttribute('aria-valuenow', '520');

    expect(Math.abs(await columnWidth(page, 'Estados') - before.workflow)).toBeLessThanOrEqual(1);
    expect(Math.abs(await columnWidth(page, 'Acciones') - before.actions)).toBeLessThanOrEqual(1);
  });

  test('resets the saved title width on double click', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.addInitScript((key) => {
      localStorage.setItem(key, JSON.stringify({ title: 416 }));
    }, WIDTH_KEY);
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const handle = page.getByTestId('documents-title-resize-handle');
    await expect(handle).toHaveAttribute('aria-valuenow', '416');
    await handle.dblclick();

    await expect(handle).toHaveAttribute('aria-valuenow', '320');
    const stored = await page.evaluate((key) => localStorage.getItem(key), WIDTH_KEY);
    expect(stored).toBeNull();
  });
});
