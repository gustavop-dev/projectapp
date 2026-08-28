/**
 * Long-title disclosure and reusable column resizing on /panel/documents.
 *
 * @flow:admin-document-title-column-resize
 * Covers: one clipped-only floating hint shared with actions, compact in-place
 *         disclosure, inventory-sized resize persistence, fixed workflow/actions
 *         tracks and double-click reset.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const WIDTH_KEY = 'projectapp-table-widths:documents-list';
const LONG_TITLE = 'Cliente Atlas — Contrato marco de servicios profesionales para el Comité Ejecutivo Regional — versión final aprobada para firma del 25 de agosto de 2026';
const INVENTORY_BOUND_TITLE = 'Contrato Cliente Atlas implementación soporte agosto 26.';
const UNBROKEN_TITLES = [
  'guia_apuntar_dominio_ux_26082026',
  'Levantamiento_Fase_4_Multi-Tenant_24082026',
  'Respuesta_Etapa_3_Inventario',
];
const LONG_FOLDER = 'Respuesta_Etapa_3_Inventario';
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

function documentFixture(id, title, overrides = {}) {
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
    ...overrides,
  };
}

const DOCUMENTS = [
  documentFixture(501, LONG_TITLE, { folder: 77, folder_name: LONG_FOLDER }),
  documentFixture(502, UNBROKEN_TITLES[0]),
  documentFixture(503, UNBROKEN_TITLES[1], { folder: 77, folder_name: LONG_FOLDER }),
  documentFixture(504, UNBROKEN_TITLES[2]),
  documentFixture(505, 'Acta breve'),
  documentFixture(506, INVENTORY_BOUND_TITLE),
];

async function mockDocuments(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/') return jsonOk(DOCUMENTS);
    if (apiPath === 'documents/counts/') {
      return jsonOk({
        documents: { active: 6, archived: 0, unfiled_active: 4, unfiled_archived: 0 },
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

async function expectInside(inner, outer) {
  await inner.scrollIntoViewIfNeeded();
  const [innerBox, outerBox] = await Promise.all([inner.boundingBox(), outer.boundingBox()]);
  expect(innerBox).not.toBeNull();
  expect(outerBox).not.toBeNull();
  expect(innerBox.x).toBeGreaterThanOrEqual(outerBox.x - 1);
  expect(innerBox.x + innerBox.width).toBeLessThanOrEqual(outerBox.x + outerBox.width + 1);
}

async function expectInsideViewport(page, locator) {
  const box = await locator.boundingBox();
  const viewport = page.viewportSize();
  expect(box).not.toBeNull();
  expect(viewport).not.toBeNull();
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.y).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);
  expect(box.y + box.height).toBeLessThanOrEqual(viewport.height);
}

async function expectVerticalSeparation(upper, lower) {
  const [upperBox, lowerBox] = await Promise.all([upper.boundingBox(), lower.boundingBox()]);
  expect(upperBox).not.toBeNull();
  expect(lowerBox).not.toBeNull();
  expect(upperBox.y + upperBox.height).toBeLessThanOrEqual(lowerBox.y + 1);
}

async function expectTableTitleContained(page) {
  const title = page.getByTestId('document-open-503');
  const folder = page.getByTestId('document-folder-badge-503');
  const titleCell = title.locator('xpath=ancestor::td[1]');
  const statesCell = page.getByTestId('doc-states-cell-503');

  await expectInside(title, titleCell);
  await expectInside(folder, titleCell);
  await expectVerticalSeparation(title, folder);

  const [titleBox, folderBox, statesBox] = await Promise.all([
    title.boundingBox(), folder.boundingBox(), statesCell.boundingBox(),
  ]);
  expect(titleBox.x + titleBox.width).toBeLessThanOrEqual(statesBox.x + 1);
  expect(folderBox.x + folderBox.width).toBeLessThanOrEqual(statesBox.x + 1);
}

async function expectCompactTableTitleContained(page) {
  const title = page.getByTestId('document-open-503');
  const folder = page.getByTestId('document-folder-badge-503');
  const metadata = page.getByTestId('document-title-meta-503');
  const titleCell = title.locator('xpath=ancestor::td[1]');

  await expectInside(title, titleCell);
  await expectInside(metadata, titleCell);
  await expectInside(folder, metadata);
  await expectVerticalSeparation(title, metadata);
}

async function expectCardTitleContained(page) {
  const card = page.getByTestId('document-card-503');
  const title = page.getByTestId('document-card-open-503');
  const folder = page.getByTestId('document-card-folder-badge-503');

  await card.scrollIntoViewIfNeeded();
  await expectInside(title, card);
  await expectInside(folder, card);
  await expectVerticalSeparation(title, folder);
}

const CONTAINMENT_PROFILES = [
  { name: 'phone', width: 412, height: 915, verify: expectCardTitleContained },
  { name: 'portrait tablet', width: 835, height: 1195, verify: expectCardTitleContained },
  { name: 'landscape tablet', width: 1195, height: 835, verify: expectCompactTableTitleContained },
  { name: 'desktop', width: 1440, height: 900, verify: expectTableTitleContained },
  { name: 'wide desktop', width: 2560, height: 1440, verify: expectTableTitleContained },
];

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

  test('shows one full-name hint only for clipped titles', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (la navegación del sidebar pertenece a los flows de layout; este caso aísla la medición de los títulos)
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const longTitle = page.getByTestId('document-open-501');
    await expect(page.getByTestId('document-open-501-toggle')).toBeVisible();
    await expect(longTitle).not.toHaveAttribute('title', /.+/);
    await longTitle.hover();
    const tooltip = page.getByRole('tooltip');
    await expect(tooltip).toHaveCount(1);
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText(LONG_TITLE);
    await expectInsideViewport(page, tooltip);

    const shortTitle = page.getByTestId('document-open-505');
    await expect(page.getByTestId('document-open-505-toggle')).toHaveCount(0);
    await expect(shortTitle).not.toHaveAttribute('title', /.+/);
    await shortTitle.hover();
    await expect(page.getByRole('tooltip')).toHaveCount(0);
  });

  test('uses the shared tooltip for a row action', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const action = page.getByTestId('doc-actions-cell-501')
      .getByRole('button', { name: `Acciones de ${LONG_TITLE}` });
    await expect(action).not.toHaveAttribute('title', /.+/);
    await action.hover();

    const tooltip = page.getByRole('tooltip');
    await expect(tooltip).toHaveCount(1);
    await expect(tooltip).toBeVisible();
    await expect(tooltip).toContainText(`Acciones de ${LONG_TITLE}`);
    await expectInsideViewport(page, tooltip);
  });

  test('offers the same full-name control for an unbroken clipped title', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const handle = page.getByTestId('documents-title-resize-handle');
    await handle.press('Home');
    await expect(handle).toHaveAttribute('aria-valuenow', '240');

    const title = page.getByTestId('document-open-503');
    const toggle = page.getByTestId('document-open-503-toggle');
    await expect(toggle).toBeVisible();
    await expect(title).not.toHaveAttribute('title', /.+/);
    await title.hover();
    await expect(page.getByRole('tooltip')).toBeVisible();
    await expect(page.getByRole('tooltip')).toContainText(UNBROKEN_TITLES[1]);
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  });

  for (const profile of CONTAINMENT_PROFILES) {
    test(`contains real unbroken names at ${profile.name} width`, {
      tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:display'],
    }, async ({ page }) => {
      // quality: allow-no-interaction (display outcome: geometry is the behavior under test)
      // quality: allow-deep-link (module navigation is covered separately; this test isolates responsive geometry)
      await page.setViewportSize({ width: profile.width, height: profile.height });
      await openDocuments(page);

      await profile.verify(page);
    });
  }

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

  test('fits the current longest inventory boundary at maximum width', {
    tag: [...ADMIN_DOCUMENT_TITLE_COLUMN_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openDocuments(page);

    const title = page.getByTestId('document-open-506');
    const toggle = page.getByTestId('document-open-506-toggle');
    await expect(toggle).toBeVisible();

    const handle = page.getByTestId('documents-title-resize-handle');
    await handle.press('End');
    await expect(handle).toHaveAttribute('aria-valuenow', '520');
    await expect(toggle).toHaveCount(0);
    await title.hover();
    await expect(page.getByRole('tooltip')).toHaveCount(0);
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
