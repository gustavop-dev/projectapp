/**
 * E2E tests for the accounting incomes filters.
 *
 * FLOW: admin-accounting-filters
 * Covers: date range, amount range, partner segmented filter, active
 *         filter count badge, reset and free-text search.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_FILTERS } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const ROWS = [
  {
    id: 1,
    concept: 'Kore - Inicio 40%',
    kind: 'expected',
    kind_label: 'Esperado',
    period: '2026-02',
    period_label: 'Febrero 2026',
    period_date: '2026-02-01',
    destination: 'partners',
    destination_label: 'Socios',
    total_amount: '1160000.00',
    gustavo_amount: '580000.00',
    carlos_amount: '580000.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    paid_amount: '1160000.00',
    pending_amount: '0.00',
    payment_status: 'paid',
    payment_status_label: 'Pagado',
    notes: '',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
  },
  {
    id: 2,
    concept: 'G&M Entrega No. 1 (Mayo)',
    kind: 'expected',
    kind_label: 'Esperado',
    period: '2026-05',
    period_label: 'Mayo 2026',
    period_date: '2026-05-01',
    destination: 'partners',
    destination_label: 'Socios',
    total_amount: '3553750.00',
    gustavo_amount: '1776875.00',
    carlos_amount: '1776875.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    paid_amount: '0.00',
    pending_amount: '3553750.00',
    payment_status: 'pending',
    payment_status_label: 'Pendiente',
    notes: '',
    created_at: '2026-05-01T10:00:00Z',
    updated_at: '2026-05-01T10:00:00Z',
  },
  {
    id: 3,
    concept: 'Vastago (Fase 1) - Inicio 40%',
    kind: 'liquid',
    kind_label: 'Líquido',
    period: '2026-04',
    period_label: 'Abril 2026',
    period_date: '2026-04-01',
    destination: 'pocket',
    destination_label: 'Bolsillo ProjectApp',
    total_amount: '2123000.00',
    gustavo_amount: '0.00',
    carlos_amount: '0.00',
    company_amount: '2123000.00',
    expected_income: null,
    pocket_movement: 7,
    paid_amount: null,
    pending_amount: null,
    payment_status: null,
    payment_status_label: null,
    notes: '',
    created_at: '2026-04-29T10:00:00Z',
    updated_at: '2026-04-29T10:00:00Z',
  },
  {
    id: 4,
    concept: 'Universidad Nacional',
    kind: 'liquid',
    kind_label: 'Líquido',
    period: '2026-02',
    period_label: 'Febrero 2026',
    period_date: '2026-02-01',
    destination: 'partners',
    destination_label: 'Socios',
    total_amount: '1400000.00',
    gustavo_amount: '1400000.00',
    carlos_amount: '0.00',
    company_amount: '0.00',
    expected_income: null,
    pocket_movement: null,
    paid_amount: null,
    pending_amount: null,
    payment_status: null,
    payment_status_label: null,
    notes: '',
    created_at: '2026-02-10T10:00:00Z',
    updated_at: '2026-02-10T10:00:00Z',
  },
];

// Saved tabs for the restorable-base test: 502 drifted away from its seeded
// definition (the auto-save wiped paymentStatus), so it filters exactly like
// 501 until restored.
const SAVED_TABS = [
  {
    id: 501, view: 'accounting_income', name: 'Todos los esperados',
    filters: { kind: 'expected' },
    base_filters: { kind: 'expected' },
    order: 0,
  },
  {
    id: 502, view: 'accounting_income', name: 'Esperados sin cobrar',
    filters: { kind: 'expected' },
    base_filters: { kind: 'expected', paymentStatus: 'pending' },
    order: 1,
  },
];

// Same view, with the placeholder row that carries a builtin's order: 601
// stands in for the code-level 'lost' chip, whose filters stay in the page.
const BUILTIN_BACKED_TABS = [
  {
    id: 601, view: 'accounting_income', name: 'Perdidos',
    filters: {}, base_filters: {}, order: 0, builtin_key: 'lost',
  },
  {
    id: 602, view: 'accounting_income', name: 'Todos los esperados',
    filters: { kind: 'expected' }, base_filters: { kind: 'expected' },
    order: 1,
  },
];

function buildHandler({ tabs = [], reorderCalls = [] } = {}) {
  return ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    // This suite was written against the flat table; pin the landing mode
    // so the production default (grouped) never reshapes what it asserts.
    if (apiPath === 'accounting/settings/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ income_default_view_mode: 'classic' }),
      };
    }
    if (apiPath === 'accounting/incomes/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: ROWS, meta: {} }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      // A move persists by posting the whole order. Echo the list back in
      // that order, the way the server does: without it the next render
      // rebuilds the strip from the old list and the move snaps back.
      if (apiPath.includes('reorder/') && method === 'POST') {
        const { ids } = route.request().postDataJSON();
        reorderCalls.push(ids);
        const byId = new Map(tabs.map((t) => [t.id, t]));
        const reordered = ids
          .map((id, index) => (byId.has(id) ? { ...byId.get(id), order: index } : null))
          .filter(Boolean);
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(reordered),
        };
      }
      if (method === 'PATCH') {
        const tabId = Number(apiPath.replace(/\/$/, '').split('/').pop());
        const tab = tabs.find((t) => t.id === tabId) || {};
        const body = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...tab, ...body }),
        };
      }
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(tabs),
      };
    }
    return null;
  };
}

async function gotoIncomes(page, options = {}) {
  await mockApi(page, buildHandler(options));
  // `=all` opts out of the "Solo esperados" landing tab: this spec drives the
  // filter panel from an unfiltered table.
  await page.goto(
    '/panel/accounting/incomes?accounting_incomeTab=all',
    { waitUntil: 'domcontentloaded' },
  );
  await expect(
    page.getByRole('heading', { name: 'Ingresos', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
  await expect(page.getByTestId('accounting-row-1')).toBeVisible();
}

function visibleRows(page) {
  return page.locator('[data-testid^="accounting-row-"]');
}

/**
 * Just the two saved chips, in DOM order. The strip also carries the page's
 * builtin quick-filters, which render among them, so `.first()` over every
 * chip would answer about "Solo esperados", not about the pair under test.
 */
function savedPair(page) {
  return page.locator(
    '[data-testid="filter-tabs-tab-501"], [data-testid="filter-tabs-tab-502"]',
  );
}

/**
 * Manual mouse drag of one chip past another — sortablejs does not react to
 * Playwright's dragTo.
 *
 * Three things this has to get right:
 * - Scroll the chip into view first. `page.mouse` takes raw viewport
 *   coordinates and does not auto-scroll the way `locator.click()` does, so a
 *   chip below the fold receives no events at all and the drag does nothing.
 * - Nudge before travelling. A first small move is what makes sortable enter
 *   drag mode; jumping straight to the target reads as a click.
 * - Land past the neighbour's midpoint but inside it. Sortable only reorders
 *   once the pointer crosses the middle, and aiming beyond the element drops
 *   outside the list, which reverts.
 */
async function dragChipPast(page, source, target) {
  await source.scrollIntoViewIfNeeded();
  const from = await source.boundingBox();
  const to = await target.boundingBox();

  await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
  await page.mouse.down();
  await page.mouse.move(from.x + from.width / 2 + 8, from.y + from.height / 2, { steps: 4 });
  await page.mouse.move(to.x + to.width * 0.75, to.y + to.height / 2, { steps: 12 });
  await page.mouse.up();
}

async function openFilterPanel(page) {
  await page.getByRole('button', { name: /Filtros/ }).click();
}

// The sortable column headers share names with the filter dropdowns
// ("Total"), so filter buttons are scoped to the panel container.
function filterPanel(page) {
  return page.getByTestId('accounting-filter-panel');
}

test.describe('Admin Accounting Filters', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('date range keeps only rows inside the period', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await filterPanel(page).getByRole('button', { name: /^Mes/ }).click();
    await page.getByPlaceholder('Desde').fill('2026-04-01');
    await page.getByPlaceholder('Hasta').fill('2026-05-31');

    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByText('G&M Entrega No. 1 (Mayo)')).toBeVisible();
    await expect(page.getByText('Kore - Inicio 40%')).toHaveCount(0);
  });

  test('amount range filters by total', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await filterPanel(page).getByRole('button', { name: /^Total/ }).click();
    await page.getByPlaceholder('Mín').fill('2000000');
    await page.getByPlaceholder('Máx').fill('4000000');

    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();
    await expect(page.getByText('Universidad Nacional')).toHaveCount(0);
  });

  test('partner segmented filter distinguishes Gustavo from ProjectApp', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Gustavo', exact: true }).click();
    await expect(visibleRows(page)).toHaveCount(3);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toHaveCount(0);

    await page.getByRole('tab', { name: 'ProjectApp' }).click();
    await expect(visibleRows(page)).toHaveCount(1);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();
  });

  test('collection filter isolates the expected rows with no payment yet', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (reaching /panel/accounting/incomes through the
    // subnav is exercised by the accounting navigation specs; this test pins
    // the collection filter itself)
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Sin pagos' }).click();

    // Only the expected row without any settlement survives: the paid one
    // and both liquid rows drop out.
    await expect(visibleRows(page)).toHaveCount(1);
    await expect(page.getByText('G&M Entrega No. 1 (Mayo)')).toBeVisible();
    await expect(page.getByText('Kore - Inicio 40%')).toHaveCount(0);

    const chip = page.getByTestId('accounting-filter-chip');
    await expect(chip).toContainText('Cobro: Sin pagos');

    await chip.getByRole('button').click();
    await expect(visibleRows(page)).toHaveCount(4);
  });

  test('restoring a drifted saved tab recovers its seeded collection filter', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await gotoIncomes(page, { tabs: SAVED_TABS });

    // Drifted "Esperados sin cobrar" behaves exactly like "Todos los esperados":
    // both expected rows survive and the dot marks the drift.
    await page.getByTestId('filter-tabs-tab-502').click();
    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByTestId('filter-tabs-modified-502')).toBeVisible();

    await page.getByTestId('filter-tabs-menu-502').click();
    await page.getByTestId('filter-tabs-restore').click();

    // The seeded definition is back: only the uncollected expected remains,
    // the Cobro chip reappears and the drift dot goes away.
    await expect(visibleRows(page)).toHaveCount(1);
    await expect(page.getByText('G&M Entrega No. 1 (Mayo)')).toBeVisible();
    await expect(
      page.getByTestId('accounting-filter-chip').filter({ hasText: 'Cobro: Sin pagos' }),
    ).toHaveCount(1);
    await expect(page.getByTestId('filter-tabs-modified-502')).toHaveCount(0);
  });

  test('active filter count badge reflects applied filters', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Líquido' }).click();
    await page.getByRole('tab', { name: 'Gustavo', exact: true }).click();

    await expect(page.getByRole('button', { name: /Filtros/ })).toContainText('2');
  });

  test('reset restores the full list', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Líquido' }).click();
    await expect(visibleRows(page)).toHaveCount(2);

    await page.getByTestId('accounting-filter-reset').click();
    await expect(visibleRows(page)).toHaveCount(4);
  });

  test('free search filters by concept', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);

    await page.getByTestId('incomes-search-input').fill('vastago');
    await expect(visibleRows(page)).toHaveCount(1, { timeout: 10_000 });
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();
  });

  test('search highlights occurrences with <mark> in the table', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);

    await page.getByTestId('incomes-search-input').fill('inicio');
    await expect(visibleRows(page)).toHaveCount(2, { timeout: 10_000 });
    const marks = page.locator('mark');
    await expect(marks).toHaveText(['Inicio', 'Inicio']);
  });

  test('shows the filtered results count', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await expect(page.getByTestId('accounting-results-count')).toHaveText('4 resultados');

    await openFilterPanel(page);
    await page.getByRole('tab', { name: 'Líquido' }).click();
    await expect(page.getByTestId('accounting-results-count')).toHaveText('2 resultados');
  });

  test('applied filters render removable chips that restore the rows', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await page.getByRole('tab', { name: 'Líquido' }).click();
    await expect(visibleRows(page)).toHaveCount(2);

    const chip = page.getByTestId('accounting-filter-chip');
    await expect(chip).toHaveCount(1);
    await expect(chip).toContainText('Tipo: Líquido');

    await chip.getByRole('button').click();
    await expect(visibleRows(page)).toHaveCount(4);
    await expect(page.getByTestId('accounting-filter-chip')).toHaveCount(0);
  });

  test('amount range filters live while typing (no blur needed)', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await filterPanel(page).getByRole('button', { name: /^Total/ }).click();
    await page.getByPlaceholder('Mín').pressSequentially('2000000');

    // Live (debounced) emission: rows shrink without leaving the input.
    await expect(visibleRows(page)).toHaveCount(2, { timeout: 10_000 });
  });

  // La tira de predefinidos se desbordaba a la derecha y el
  // `body { overflow-x: hidden }` de app.vue la recortaba SIN barra de scroll:
  // los últimos filtros quedaban inalcanzables y el corte se leía como el final
  // de la lista. 1024px está por encima del breakpoint `md`, que es donde vive
  // la tira de escritorio y donde se veía el defecto.
  test('ningún filtro predefinido queda recortado en una ventana angosta', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (el defecto se manifiesta al pintar: los
    // filtros del final ya están recortados antes de que el usuario toque nada,
    // y cualquier clic previo taparía justo lo que se quiere medir. El uso del
    // último predefinido lo cubre el test de al lado.)
    // quality: allow-deep-link (medimos el ancho de la tira al entrar, que es
    // cuando el corte engaña; la ruta de navegación la cubren los demás tests.)
    await page.setViewportSize({ width: 1024, height: 720 });
    await gotoIncomes(page, { tabs: SAVED_TABS });

    const tabs = page.locator('[data-testid^="filter-tabs-tab-"]');
    await expect(tabs).toHaveCount(7);
    await expect(tabs.last()).toContainText('Esperados sin cobrar');

    // El veredicto: si la tira desbordara, scrollWidth superaría a clientWidth
    // y lo que sobra estaría recortado sin que nada lo anuncie.
    const strip = page.getByTestId('filter-tabs-strip');
    const { scrollWidth, clientWidth } = await strip.evaluate((el) => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
    }));
    expect(
      scrollWidth,
      `la tira desborda su contenedor (scrollWidth=${scrollWidth}, clientWidth=${clientWidth})`,
    ).toBeLessThanOrEqual(clientWidth + 1);
  });

  test('el último filtro predefinido se puede usar en una ventana angosta', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 720 });
    await gotoIncomes(page, { tabs: SAVED_TABS });

    await page.locator('[data-testid^="filter-tabs-tab-"]').last().click();

    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toHaveCount(0);
  });
  test('reordenar la tira arrastrando un filtro guardado', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (la interacción es un arrastre manual de
    // mouse — sortablejs ignora el dragTo de Playwright, así que esto maneja
    // mouse.down/move/up, que la lista de llamadas del detector no reconoce)
    const reorderCalls = [];
    await gotoIncomes(page, { tabs: SAVED_TABS, reorderCalls });

    const first = page.getByTestId('filter-tabs-tab-501');
    const second = page.getByTestId('filter-tabs-tab-502');
    await expect(first).toBeVisible();
    await dragChipPast(page, first, second);

    // El servidor recibe el orden nuevo, y la tira lo muestra.
    await expect
      .poll(() => reorderCalls.length, { timeout: 10_000 })
      .toBeGreaterThan(0);
    expect(reorderCalls[0]).toEqual([502, 501]);
    await expect(savedPair(page).first()).toContainText('Esperados sin cobrar');
  });

  test('arrastrar un filtro no lo aplica', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // Punto 2 de la ficha: mover y seleccionar arrancan con el mismo gesto, y
    // la tira cambia toda la vista — un arrastre no puede filtrarla al pasar.
    // quality: allow-no-interaction (ídem: arrastre manual con mouse.down/
    // move/up, que el detector no cuenta como interacción)
    const reorderCalls = [];
    await gotoIncomes(page, { tabs: SAVED_TABS, reorderCalls });

    await expect(visibleRows(page)).toHaveCount(4);
    await dragChipPast(
      page,
      page.getByTestId('filter-tabs-tab-501'),
      page.getByTestId('filter-tabs-tab-502'),
    );
    await expect
      .poll(() => reorderCalls.length, { timeout: 10_000 })
      .toBeGreaterThan(0);

    // La tabla sigue sin filtrar: el arrastre movió, no seleccionó.
    await expect(visibleRows(page)).toHaveCount(4);
    await expect(page).toHaveURL(/accounting_incomeTab=all/);
  });

  test('mover un filtro a la derecha desde su menú', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // La vía sin arrastrar, que es la única alcanzable para quien no puede
    // arrastrar y la cómoda en una pantalla chica.
    const reorderCalls = [];
    await gotoIncomes(page, { tabs: SAVED_TABS, reorderCalls });

    await page.getByTestId('filter-tabs-menu-501').click();
    await page.getByTestId('filter-tabs-move-right-501').click();

    await expect
      .poll(() => reorderCalls.length, { timeout: 10_000 })
      .toBeGreaterThan(0);
    expect(reorderCalls[0]).toEqual([502, 501]);
    await expect(savedPair(page).first()).toContainText('Esperados sin cobrar');
  });

  test('un predefinido de fábrica se mueve igual que uno propio', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // Punto 4: los builtin viven en el código y su orden en una fila
    // placeholder, así que se mueven junto a los guardados.
    const reorderCalls = [];
    await gotoIncomes(page, { tabs: BUILTIN_BACKED_TABS, reorderCalls });

    await page.getByTestId('filter-tabs-menu-lost').click();
    await page.getByTestId('filter-tabs-move-right-lost').click();

    await expect
      .poll(() => reorderCalls.length, { timeout: 10_000 })
      .toBeGreaterThan(0);
    // 601 es la fila placeholder de 'lost': el chip viaja por su builtin_key.
    expect(reorderCalls[0]).toEqual([602, 601]);
  });
});
