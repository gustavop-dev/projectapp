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

function buildHandler({ tabs = [], rows = ROWS } = {}) {
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
        body: JSON.stringify({ results: rows, meta: {} }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
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

async function openFilterPanel(page) {
  await page.getByRole('button', { name: /Filtros/ }).click();
}

// The sortable column headers share names with the filter dropdowns
// ("Total"), so filter buttons are scoped to the panel container.
function filterPanel(page) {
  return page.getByTestId('accounting-filter-panel');
}

/**
 * One option of a filter dimension.
 *
 * The dimensions are checkable toggle groups (`role="group"` + `aria-pressed`),
 * not tablists — several values of one dimension can be marked at once. Scoping
 * by the group's accessible name is what keeps "Gustavo" the socio apart from
 * "Personal Gustavo" the contabilidad, and from the saved tab of the same name.
 */
function filterOption(page, dimension, label) {
  return filterPanel(page)
    .getByRole('group', { name: dimension })
    .getByRole('button', { name: label, exact: true });
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

    await filterOption(page, 'Socio', 'Gustavo').click();
    await expect(visibleRows(page)).toHaveCount(3);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toHaveCount(0);

    // Marking a second socio ADDS it — the dimension is checkable now, so
    // clicking ProjectApp no longer silently replaces Gustavo.
    await filterOption(page, 'Socio', 'ProjectApp').click();
    await expect(visibleRows(page)).toHaveCount(4);
    await expect(page.getByText('Vastago (Fase 1) - Inicio 40%')).toBeVisible();

    // Unmarking Gustavo leaves ProjectApp's own cut behind.
    await filterOption(page, 'Socio', 'Gustavo').click();
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

    await filterOption(page, 'Cobro', 'Sin pagos').click();

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

    await filterOption(page, 'Tipo', 'Líquido').click();
    await filterOption(page, 'Socio', 'Gustavo').click();

    await expect(page.getByRole('button', { name: /Filtros/ })).toContainText('2');
  });

  test('reset restores the full list', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await filterOption(page, 'Tipo', 'Líquido').click();
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
    await filterOption(page, 'Tipo', 'Líquido').click();
    await expect(page.getByTestId('accounting-results-count')).toHaveText('2 resultados');
  });

  test('applied filters render removable chips that restore the rows', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await gotoIncomes(page);
    await openFilterPanel(page);

    await filterOption(page, 'Tipo', 'Líquido').click();
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

  // ── Selección múltiple dentro de una misma dimensión ──────────────────────
  //
  // El caso de la ficha: "Cobro" sólo admitía un valor, así que la vista de
  // esperados por cobrar dejaba fuera a los parcialmente pagados. Un abono
  // recién registrado desaparecía y parecía no haberse creado nunca.

  const PARTIAL_ROWS = [
    { ...ROWS[1] },
    {
      ...ROWS[1],
      id: 9,
      concept: 'Abonado a medias',
      total_amount: '1000000.00',
      paid_amount: '400000.00',
      pending_amount: '600000.00',
      payment_status: 'partial',
      payment_status_label: 'Parcial',
    },
    { ...ROWS[0] },
  ];

  test('two values of one dimension show the union of both cuts', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (llegar a Ingresos por el subnav ya lo cubren
    // las specs de navegación; ésta fija la selección múltiple en sí)
    await gotoIncomes(page, { rows: PARTIAL_ROWS });
    await openFilterPanel(page);

    await filterOption(page, 'Cobro', 'Sin pagos').click();
    await expect(visibleRows(page)).toHaveCount(1);
    await expect(page.getByText('Abonado a medias')).toHaveCount(0);

    // Marking a second value ADDS to the cut instead of replacing it.
    await filterOption(page, 'Cobro', 'Parcial').click();
    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByText('G&M Entrega No. 1 (Mayo)')).toBeVisible();
    await expect(page.getByText('Abonado a medias')).toBeVisible();
    // The one that IS collected stays out: the dimension still narrows.
    await expect(page.getByText('Kore - Inicio 40%')).toHaveCount(0);

    await expect(filterOption(page, 'Cobro', 'Sin pagos'))
      .toHaveAttribute('aria-pressed', 'true');
    await expect(filterOption(page, 'Cobro', 'Parcial'))
      .toHaveAttribute('aria-pressed', 'true');
  });

  test('one chip lists both values and drops them one at a time', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (llegar a Ingresos por el subnav ya lo cubren
    // las specs de navegación; ésta fija la selección múltiple en sí)
    await gotoIncomes(page, { rows: PARTIAL_ROWS });
    await openFilterPanel(page);
    await filterOption(page, 'Cobro', 'Sin pagos').click();
    await filterOption(page, 'Cobro', 'Parcial').click();

    const chip = page.getByTestId('accounting-filter-chip');
    await expect(chip).toHaveCount(1);
    await expect(chip).toHaveText('Cobro: Sin pagos, Parcial');

    // Quitar un valor no desarma la dimensión completa.
    await page
      .getByTestId('accounting-filter-chip-remove-paymentStatus-pending')
      .click();
    await expect(chip).toHaveText('Cobro: Parcial');
    await expect(visibleRows(page)).toHaveCount(1);
    await expect(page.getByText('Abonado a medias')).toBeVisible();
  });

  test('"Todos" clears the dimension instead of adding a value to it', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (llegar a Ingresos por el subnav ya lo cubren
    // las specs de navegación; ésta fija la selección múltiple en sí)
    await gotoIncomes(page, { rows: PARTIAL_ROWS });
    await openFilterPanel(page);
    await filterOption(page, 'Cobro', 'Sin pagos').click();
    await filterOption(page, 'Cobro', 'Parcial').click();
    await expect(visibleRows(page)).toHaveCount(2);

    await filterOption(page, 'Cobro', 'Todos').click();
    await expect(visibleRows(page)).toHaveCount(3);
    await expect(page.getByTestId('accounting-filter-chip')).toHaveCount(0);
  });

  test('the multi-value cut survives being shared as a link', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (el enlace compartido ES la funcionalidad bajo
    // prueba: llegar clicando ejercitaría el otro camino, no éste)
    // quality: allow-no-interaction (el contrato es que la URL basta; tocar
    // algo antes taparía justo lo que se quiere verificar)
    // A saved filter is only worth having if it can be pasted to someone else.
    await mockApi(page, buildHandler({ rows: PARTIAL_ROWS }));
    await page.goto(
      '/panel/accounting/incomes?accounting_incomeTab=all'
      + '&paymentStatus=pending,partial',
      { waitUntil: 'domcontentloaded' },
    );
    await expect(
      page.getByRole('heading', { name: 'Ingresos', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    await expect(visibleRows(page)).toHaveCount(2);
    await expect(page.getByTestId('accounting-filter-chip'))
      .toHaveText('Cobro: Sin pagos, Parcial');
  });

  test('the landing tab no longer hides a partially paid expected', {
    tag: [...ADMIN_ACCOUNTING_FILTERS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (la pestaña de aterrizaje se define por la ruta
    // desnuda; entrar por el subnav no probaría el default que aquí importa)
    // quality: allow-no-interaction (el defecto era lo que se ve AL LLEGAR: el
    // parcial faltaba sin que nadie tocara un filtro)
    // Sin `?...Tab=all`: se entra por donde entra el operador todos los días.
    await mockApi(page, buildHandler({ rows: PARTIAL_ROWS }));
    await page.goto(
      '/panel/accounting/incomes',
      { waitUntil: 'domcontentloaded' },
    );
    await expect(
      page.getByRole('heading', { name: 'Ingresos', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    await expect(page.getByText('Abonado a medias')).toBeVisible();
    await expect(page.getByText('G&M Entrega No. 1 (Mayo)')).toBeVisible();
    await expect(page.getByText('Kore - Inicio 40%')).toHaveCount(0);
  });
});
