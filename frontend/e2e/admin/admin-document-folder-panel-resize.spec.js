/**
 * E2E tests for the resizable folder panel on /panel/documents.
 *
 * @flow:admin-document-folder-panel-resize
 * Covers: default width fits the real longest folder names untruncated
 *         (22-char guarantee, measured from the live inventory), drag handle
 *         resize with clamp + localStorage persistence across reloads,
 *         double-click reset, keyboard resize, and the compact drawer where
 *         the desktop handle does not render and the stored width is ignored.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const STORAGE_KEY = 'projectapp-documents-folder-width';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function folder(overrides) {
  return {
    id: 0, name: '', slug: '', parent: null, order: 0,
    is_archived: false, archived_at: null, archived_cause: null,
    document_count: 0, children_count: 0,
    active_document_count: 0, active_children_count: 0,
    archived_document_count: 0, archived_children_count: 0,
    ...overrides,
  };
}

// Los nombres más largos del inventario real (16-ago-2026). «Futuros
// Requerimientos» (22 caracteres) es el peor caso geométrico: nombre máximo
// con AMBOS contadores visibles y conteo de documentos de dos dígitos.
const FOLDER_FUTUROS = folder({
  id: 31, name: 'Futuros Requerimientos', slug: 'futuros-requerimientos', order: 0,
  document_count: 12, active_document_count: 12,
  children_count: 1, active_children_count: 1,
});
const FOLDER_KAFE = folder({
  id: 32, name: 'Kafe Sistemas Project', slug: 'kafe-sistemas-project', order: 1,
  document_count: 34, active_document_count: 34,
});
const FOLDER_ESTIMATES = folder({
  id: 33, name: 'Requirement Estimates', slug: 'requirement-estimates', order: 2,
  document_count: 56, active_document_count: 56,
});
const FOLDER_FASE = folder({
  id: 34, name: 'Fase 1.5', slug: 'fase-1-5', parent: 31, order: 0,
  document_count: 3, active_document_count: 3,
});

const LONG_NAMES = [FOLDER_FUTUROS.name, FOLDER_KAFE.name, FOLDER_ESTIMATES.name];

function jsonOk(body) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
}

async function mockDocumentsApi(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'documents/') return jsonOk([]);
    if (apiPath === 'document-folders/') {
      return jsonOk([FOLDER_FUTUROS, FOLDER_KAFE, FOLDER_ESTIMATES, FOLDER_FASE]);
    }
    if (apiPath === 'document-tags/') return jsonOk([]);
    return null;
  });
}

async function panelWidth(page) {
  const box = await page.getByTestId('folder-panel').boundingBox();
  return box.width;
}

async function dragHandleTo(page, clientX) {
  const handle = page.getByTestId('folder-panel-resize-handle');
  const box = await handle.boundingBox();
  const y = box.y + box.height / 2;
  await page.mouse.move(box.x + box.width / 2, y);
  await page.mouse.down();
  await page.mouse.move(clientX, y, { steps: 5 });
  await page.mouse.up();
}

test.describe('Admin Document Folder Panel Resize', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8702, role: 'admin', is_staff: true },
    });
  });

  test('shows the longest real folder names untruncated at the default width', {
    tag: [...ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (los specs del panel de documentos entran directo a la ruta, como toda la carpeta admin/*; la navegación por el sidebar la cubren los specs de layout)
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    const panel = page.getByTestId('folder-panel');
    // 30s en la primera espera: la primera visita compila la página en el dev
    // server (Vite on-demand) y en frío supera los 15s del timeout por defecto.
    await expect(panel).toBeVisible({ timeout: 30_000 });
    const box = await panel.boundingBox();
    expect(Math.abs(box.width - 384)).toBeLessThanOrEqual(2);

    // La garantía se mide con la webfont ya aplicada: con la fallback los
    // anchos mienten en los dos sentidos.
    await page.evaluate(() => document.fonts.ready);

    const list = page.getByTestId('folder-list');
    for (const name of LONG_NAMES) {
      const span = list.getByTitle(name);
      await expect(span).toHaveText(name);
      const m = await span.evaluate((el) => ({ sw: el.scrollWidth, cw: el.clientWidth }));
      expect(
        m.sw,
        `«${name}» debe leerse completo al ancho por defecto (scrollWidth=${m.sw}, clientWidth=${m.cw})`,
      ).toBeLessThanOrEqual(m.cw);
    }

    // Peor caso: la fila activa pasa a font-medium y el mismo nombre es más ancho.
    const worstRow = list.getByRole('button', { name: /^Futuros Requerimientos/ });
    await worstRow.click();
    await expect(worstRow).toHaveAttribute('aria-current', /.+/);
    const active = await list.getByTitle(FOLDER_FUTUROS.name)
      .evaluate((el) => ({ sw: el.scrollWidth, cw: el.clientWidth }));
    expect(
      active.sw,
      `la fila activa (font-medium) también debe leerse completa (scrollWidth=${active.sw}, clientWidth=${active.cw})`,
    ).toBeLessThanOrEqual(active.cw);
  });

  test('widens the panel by dragging and keeps the width across a reload', {
    tag: [...ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (el arrastre ES la interacción: page.mouse down/move/up sobre la manija con pointer capture; la lista click/fill/press del gate no registra drags manuales — mismo caso que admin-document-drag-organize)
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');
    await expect(page.getByTestId('folder-panel')).toBeVisible({ timeout: 30_000 });

    // +60 y no más: con el default en 384 hay ~96px hasta el tope de 480, y
    // este test prueba el ensanche libre — el clamp tiene su propio test.
    const handleBox = await page.getByTestId('folder-panel-resize-handle').boundingBox();
    await dragHandleTo(page, handleBox.x + handleBox.width / 2 + 60);

    const widened = await panelWidth(page);
    expect(widened).toBeGreaterThan(430);
    expect(widened).toBeLessThan(470);

    const stored = await page.evaluate((key) => window.localStorage.getItem(key), STORAGE_KEY);
    expect(Math.abs(Number(stored) - widened)).toBeLessThanOrEqual(2);

    await page.reload({ waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('folder-panel')).toBeVisible({ timeout: 30_000 });
    const restored = await panelWidth(page);
    expect(Math.abs(restored - Number(stored))).toBeLessThanOrEqual(2);

    // El panel reconstruido con el ancho elegido sigue mostrando los datos del
    // fixture: el conteo recursivo de «Futuros Requerimientos» (12 + 3).
    await expect(
      page.getByTestId('folder-list').getByTestId('folder-document-count').first(),
    ).toHaveText('15');
  });

  test('clamps the drag at 240 and 480', {
    tag: [...ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (el arrastre ES la interacción: page.mouse down/move/up sobre la manija con pointer capture; la lista click/fill/press del gate no registra drags manuales — mismo caso que admin-document-drag-organize)
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');
    const panel = page.getByTestId('folder-panel');
    // 30s en la primera espera: la primera visita compila la página en el dev
    // server (Vite on-demand) y en frío supera los 15s del timeout por defecto.
    await expect(panel).toBeVisible({ timeout: 30_000 });
    const panelBox = await panel.boundingBox();

    // Muy a la izquierda: pide ~50px, el clamp responde el mínimo.
    await dragHandleTo(page, panelBox.x + 50);
    expect(Math.abs(await panelWidth(page) - 240)).toBeLessThanOrEqual(2);

    // Muy a la derecha: pide ~700px, el clamp responde el máximo.
    await dragHandleTo(page, panelBox.x + 700);
    expect(Math.abs(await panelWidth(page) - 480)).toBeLessThanOrEqual(2);

    const stored = await page.evaluate((key) => window.localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBe('480');

    // Al ancho máximo el contenido del fixture sigue ahí: la única subcarpeta
    // del inventario es la de «Futuros Requerimientos».
    await expect(page.getByTestId('folder-list').getByTestId('folder-subfolder-count')).toHaveText('1');
  });

  test('double-click on the handle resets the width and clears the stored value', {
    tag: [...ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.addInitScript((key) => {
      window.localStorage.setItem(key, '420');
    }, STORAGE_KEY);
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    // El valor sembrado se restaura antes de tocar nada.
    await expect(page.getByTestId('folder-panel')).toBeVisible({ timeout: 30_000 });
    expect(Math.abs(await panelWidth(page) - 420)).toBeLessThanOrEqual(2);

    await page.getByTestId('folder-panel-resize-handle').dblclick();

    expect(Math.abs(await panelWidth(page) - 384)).toBeLessThanOrEqual(2);
    const stored = await page.evaluate((key) => window.localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBeNull();

    // Volver al default es volver al ancho garantizado: el nombre de 21
    // caracteres sigue completo tras el reset.
    await expect(
      page.getByTestId('folder-list').getByTitle(FOLDER_KAFE.name),
    ).toHaveText(FOLDER_KAFE.name);
  });

  test('resizes with the keyboard and persists each step', {
    tag: [...ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');
    await expect(page.getByTestId('folder-panel')).toBeVisible({ timeout: 30_000 });

    const handle = page.getByTestId('folder-panel-resize-handle');
    await handle.focus();
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowRight');

    expect(Math.abs(await panelWidth(page) - 416)).toBeLessThanOrEqual(2);
    let stored = await page.evaluate((key) => window.localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBe('416');

    await page.keyboard.press('Home');
    expect(Math.abs(await panelWidth(page) - 240)).toBeLessThanOrEqual(2);
    stored = await page.evaluate((key) => window.localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBe('240');

    // Incluso al mínimo, los datos del fixture siguen renderizados en la fila.
    await expect(page.getByTestId('folder-list').getByTestId('folder-subfolder-count')).toHaveText('1');
  });

  test('ignores the saved desktop width when folders open in the compact drawer', {
    tag: [...ADMIN_DOCUMENT_FOLDER_PANEL_RESIZE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (los specs del panel de documentos entran directo a la ruta, como toda la carpeta admin/*; la navegación por el sidebar la cubren los specs de layout)
    await page.addInitScript((key) => {
      window.localStorage.setItem(key, '480');
    }, STORAGE_KEY);
    await page.setViewportSize({ width: 800, height: 900 });
    await mockDocumentsApi(page);
    await page.goto('/panel/documents');

    const trigger = page.getByTestId('folder-drawer-trigger');
    await expect(trigger).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('folder-panel')).toHaveCount(0);
    await expect(page.getByTestId('folder-panel-resize-handle')).toHaveCount(0);

    await trigger.click();
    const drawer = page.getByTestId('folder-drawer');
    await expect(drawer).toContainText(FOLDER_FUTUROS.name);

    // El cajón usa su ancho canónico de 384px, no los 480px guardados para
    // la columna de escritorio.
    const box = await drawer.boundingBox();
    expect(Math.abs(box.width - 384)).toBeLessThanOrEqual(2);
  });
});
