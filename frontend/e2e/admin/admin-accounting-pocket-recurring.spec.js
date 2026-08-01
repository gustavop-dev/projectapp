/**
 * E2E tests for the pocket ledger and recurring payments subviews.
 *
 * FLOWS: admin-accounting-pocket, admin-accounting-recurring
 * Covers: pocket balance card, running-balance ledger, linked-movement
 *         editing (ledger prefill + locked direction); recurring totals
 *         cards and the currency-dependent COP-equivalent field in the
 *         modal.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_POCKET,
  ADMIN_ACCOUNTING_RECURRING,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const POCKET_ROWS = [
  {
    id: 1,
    concept: 'Vastago (Fase 1) - Inicio 40%',
    movement_date: '2026-04-29',
    direction: 'in',
    direction_label: 'Ingreso',
    amount: '2123000.00',
    is_auto_managed: true,
    linked_income_id: 11,
    linked_expense_id: null,
    linked_ledger: 'company',
    notes: '',
    created_at: '2026-04-29T10:00:00Z',
    updated_at: '2026-04-29T10:00:00Z',
  },
  {
    id: 2,
    concept: 'Pago T.C Rappi',
    movement_date: '2026-05-06',
    direction: 'out',
    direction_label: 'Egreso',
    amount: '2272000.00',
    is_auto_managed: false,
    linked_income_id: null,
    linked_expense_id: null,
    linked_ledger: null,
    notes: '',
    created_at: '2026-05-06T10:00:00Z',
    updated_at: '2026-05-06T10:00:00Z',
  },
];

const RECURRING_CATEGORIES = [
  { id: 1, name: 'Suscripciones de IA', slug: 'suscripciones-de-ia', order: 0, payment_count: 2 },
  { id: 2, name: 'Arquitectura e infraestructura', slug: 'infra', order: 1, payment_count: 1 },
];

function recurringRow(overrides) {
  return {
    price: '200.00',
    currency: 'USD',
    cop_equivalent: '800000.00',
    payment_method: 'credit_card',
    payment_method_label: 'T.C',
    frequency: 'monthly',
    frequency_label: 'Mensual',
    billing_day: 8,
    cost_type: 'fixed',
    cost_type_label: 'Fijo',
    monthly_price: '200.00',
    monthly_cop_cost: '800000.00',
    is_active: true,
    notes: '',
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-01-01T10:00:00Z',
    ...overrides,
  };
}

// Ordered the way the API returns them: category order, then manual slot.
const RECURRING_ROWS = [
  recurringRow({
    id: 1, name: 'Claude Code 20x', category: 1,
    category_name: 'Suscripciones de IA', order: 0,
  }),
  recurringRow({
    id: 2, name: 'Chat-GPT', category: 1, category_name: 'Suscripciones de IA',
    order: 1, price: '20.00', cop_equivalent: '80000.00',
    monthly_price: '20.00', monthly_cop_cost: '80000.00',
  }),
  // A biennial charge: the raw price and the monthly cost differ by 24x, which
  // is the whole point of the normalized columns.
  recurringRow({
    id: 3, name: 'Hostinger', category: 2,
    category_name: 'Arquitectura e infraestructura', order: 0,
    price: '789600.00', currency: 'COP', cop_equivalent: '789600.00',
    frequency: 'biennial', frequency_label: 'Cada 2 años',
    monthly_price: '32900.00', monthly_cop_cost: '32900.00',
  }),
];

function buildHandler({ calls, reorderStatus = 200 }) {
  return async ({ route, apiPath, method }) => {
    if (apiPath.startsWith('accounting/recurring-categories/') && apiPath.endsWith('/delete/')) {
      calls.push({ apiPath, method });
      // The catalog refuses to drop a category still in use.
      return {
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'La categoría tiene 2 pago(s) recurrente(s). '
            + 'Muévelos a otra categoría antes de borrarla.',
          payment_count: 2,
        }),
      };
    }
    if (apiPath === 'accounting/recurring-categories/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: RECURRING_CATEGORIES, meta: {} }),
      };
    }
    if (apiPath === 'accounting/recurring/reorder/' && method === 'POST') {
      calls.push({ apiPath, method, body: route.request().postDataJSON() });
      return {
        status: reorderStatus,
        contentType: 'application/json',
        body: reorderStatus === 200
          ? JSON.stringify({ reordered: 3 })
          : JSON.stringify({ error: 'No se pudo guardar' }),
      };
    }
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath === 'accounting/pocket/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: POCKET_ROWS,
          meta: { balance: '-149000.00' },
        }),
      };
    }
    if (apiPath === 'accounting/recurring/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: RECURRING_ROWS,
          meta: { monthly_cop_total: '912900.00' },
        }),
      };
    }
    if (apiPath === 'accounting/recurring/create/' && method === 'POST') {
      const body = route.request().postDataJSON();
      calls.push({ apiPath, method, body });
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...RECURRING_ROWS[0], id: 99, ...body }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

/**
 * Manual mouse drag — sortablejs does not react to Playwright's dragTo.
 *
 * Two things this has to get right:
 * - Scroll first. `page.mouse` takes raw viewport coordinates and does not
 *   auto-scroll the way `locator.click()` does, so a row below the fold
 *   receives no events at all and the drag silently does nothing.
 * - Drop just inside the target's top edge. Sortable only reorders once the
 *   pointer crosses the neighbour's midpoint, and aiming past the element
 *   entirely drops outside the list, which reverts.
 */
async function dragAbove(page, sourceHandle, targetRow) {
  await sourceHandle.scrollIntoViewIfNeeded();
  const sourceBox = await sourceHandle.boundingBox();
  const targetBox = await targetRow.boundingBox();
  const x = targetBox.x + targetBox.width / 2;
  const startX = sourceBox.x + sourceBox.width / 2;
  const startY = sourceBox.y + sourceBox.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  // A small first move is what makes sortable enter drag mode.
  await page.mouse.move(startX, startY - 6, { steps: 4 });
  await page.mouse.move(x, targetBox.y + targetBox.height / 2, { steps: 10 });
  // Stay inside the target row, just above its midpoint.
  await page.mouse.move(x, targetBox.y + 3, { steps: 10 });
  await page.mouse.up();
}

/**
 * Reach a subview the way an operator does — through the accounting subnav —
 * rather than deep-linking, so the test also proves the tab is reachable.
 */
async function openSubview(page, key) {
  const entry = key === 'recurring' ? 'pocket' : 'recurring';
  await page.goto(`/panel/accounting/${entry}`, { waitUntil: 'domcontentloaded' });
  await page.getByTestId(`accounting-subnav-${key}`).click();
}

test.describe('Admin Accounting Pocket & Recurring', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('pocket balance card shows the ledger balance', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await openSubview(page, 'pocket');

    await expect(
      page.getByRole('heading', { name: 'Bolsillo ProjectApp', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByTestId('pocket-balance')).toBeVisible();
    await expect(page.getByText('Saldo del bolsillo')).toBeVisible();
  });

  test('ledger renders movements with a running balance column', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await openSubview(page, 'pocket');

    await expect(page.getByTestId('accounting-row-1')).toBeVisible({ timeout: 25_000 });
    await expect(page.getByRole('columnheader', { name: 'Saldo' })).toBeVisible();
    await expect(page.getByText('Pago T.C Rappi')).toBeVisible();
  });

  test('linked movements open the edit modal with direction locked', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/pocket', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('accounting-row-1')).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('accounting-edit-1').click();

    const modal = page.getByRole('dialog');
    await expect(
      modal.getByRole('heading', { name: 'Editar Movimiento de bolsillo' }),
    ).toBeVisible();
    await expect(
      modal.getByText('La dirección se fija al crear el movimiento vinculado.'),
    ).toBeVisible();
    await expect(modal.getByTestId('pocket-movement-ledger')).toBeVisible();
    await expect(
      modal.getByRole('tab', { name: 'Empresa', exact: true }),
    ).toHaveAttribute('aria-selected', 'true');
  });

  test('new movement modal offers the ledger selector for egresos', {
    tag: [...ADMIN_ACCOUNTING_POCKET, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/pocket', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('pocket-new-button')).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('pocket-new-button').click();
    const modal = page.getByRole('dialog');
    await expect(
      modal.getByRole('heading', { name: 'Nuevo Movimiento de bolsillo' }),
    ).toBeVisible();

    // IN movements are company-only; the selector unlocks for egresos.
    await expect(
      modal.getByText('Los ingresos al bolsillo siempre son de la empresa.'),
    ).toBeVisible();
    await modal.getByRole('tab', { name: 'Egreso', exact: true }).click();
    // For egresos the selector attributes the draw to a partner.
    await expect(modal.getByText('Atribuir a')).toBeVisible();
    await modal.getByRole('tab', { name: 'Gustavo', exact: true }).click();
    await expect(
      modal.getByRole('tab', { name: 'Gustavo', exact: true }),
    ).toHaveAttribute('aria-selected', 'true');
  });

  test('recurring subview shows monthly cost and the breakdown card', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the helper lands on a sibling accounting
    // tab and then clicks the subnav, which is the navigation being
    // asserted; there is no pre-auth entry point in these mocked specs)
    await mockApi(page, buildHandler({ calls: [] }));
    await openSubview(page, 'recurring');

    await expect(
      page.getByRole('heading', { name: 'Pagos recurrentes', exact: true }),
    ).toBeVisible({ timeout: 25_000 });
    await expect(page.getByText('Costo mensual (COP)')).toBeVisible();
    await expect(page.getByText('Desglose mensual')).toBeVisible();
    await expect(page.getByTestId('recurring-breakdown')).toBeVisible();
    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
  });

  test('grouped view lists each category with its monthly subtotal', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the helper lands on a sibling accounting
    // tab and then clicks the subnav, which is the navigation being
    // asserted; there is no pre-auth entry point in these mocked specs)
    await mockApi(page, buildHandler({ calls: [] }));
    await openSubview(page, 'recurring');
    await expect(page.getByTestId('accounting-row-1')).toBeVisible({ timeout: 25_000 });

    // Grouped is the default view.
    await expect(page.getByTestId('recurring-group-1')).toContainText('Suscripciones de IA');
    await expect(page.getByTestId('recurring-group-2'))
      .toContainText('Arquitectura e infraestructura');

    // 800.000 + 80.000 in the AI group; the biennial Hostinger contributes its
    // prorated 32.900, not the 789.600 it is charged.
    await expect(page.getByTestId('recurring-group-total-1')).toHaveText('$880.000 COP');
    await expect(page.getByTestId('recurring-group-total-2')).toHaveText('$32.900 COP');
    await expect(page.getByTestId('recurring-monthly-grand-total'))
      .toHaveText('$912.900 COP');
  });

  test('monthly columns normalize a biennial charge', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the helper lands on a sibling accounting
    // tab and then clicks the subnav, which is the navigation being
    // asserted; there is no pre-auth entry point in these mocked specs)
    await mockApi(page, buildHandler({ calls: [] }));
    await openSubview(page, 'recurring');
    await expect(page.getByTestId('accounting-row-3')).toBeVisible({ timeout: 25_000 });

    await expect(page.getByRole('columnheader', { name: 'Precio mensual' })).toBeVisible();
    await expect(
      page.getByRole('columnheader', { name: 'Equiv. COP mensual' }),
    ).toBeVisible();

    const hostinger = page.getByTestId('accounting-row-3');
    await expect(hostinger).toContainText('$789.600 COP');
    await expect(hostinger).toContainText('$32.900 COP');
  });

  test('switching to the classic view restores sorting and pagination', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (subnav navigation into Recurrentes is
    // covered by the display specs above; this one pins behavior inside
    // the tab)
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recurring-group-1')).toBeVisible({ timeout: 25_000 });

    await page.getByRole('tab', { name: 'Clásico', exact: true }).click();

    // No group headers; a sortable column header instead.
    await expect(page.getByTestId('recurring-group-1')).toHaveCount(0);
    await expect(page.getByTestId('accounting-sort-monthly_cop_cost')).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Categoría' })).toBeVisible();
  });

  test('drag handles disappear while a filter narrows the list', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (subnav navigation into Recurrentes is
    // covered by the display specs above; this one pins behavior inside
    // the tab)
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recurring-drag-handle-1')).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-search-input').fill('Hostinger');

    await expect(page.getByTestId('recurring-reorder-hint')).toBeVisible();
    await expect(page.getByTestId('recurring-drag-handle-3')).toHaveCount(0);
  });

  test('dragging a row persists the new manual order', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (the interaction is a manual mouse drag —
    // sortablejs ignores Playwright's dragTo, so this drives mouse.down/move/up,
    // which the detector's call list does not recognize)
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recurring-drag-handle-2')).toBeVisible({ timeout: 25_000 });

    // Chat-GPT (id 2) is the second row of its category; drag it above
    // Claude Code 20x (id 1).
    await dragAbove(
      page,
      page.getByTestId('recurring-drag-handle-2'),
      page.getByTestId('accounting-row-1'),
    );

    await expect
      .poll(() => calls.filter((c) => c.apiPath === 'accounting/recurring/reorder/').length)
      .toBeGreaterThan(0);
    const body = calls.find((c) => c.apiPath === 'accounting/recurring/reorder/').body;
    // Chat-GPT now leads its category; every item carries its category so a
    // cross-group move would persist too.
    expect(body.items).toEqual([
      { id: 2, category: 1, order: 0 },
      { id: 1, category: 1, order: 1 },
      { id: 3, category: 2, order: 0 },
    ]);
  });

  test('a failed reorder warns and snaps the row back', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (manual mouse drag; see the success case)
    const calls = [];
    await mockApi(page, buildHandler({ calls, reorderStatus: 500 }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recurring-drag-handle-2')).toBeVisible({ timeout: 25_000 });

    await dragAbove(
      page,
      page.getByTestId('recurring-drag-handle-2'),
      page.getByTestId('accounting-row-1'),
    );

    await expect(page.getByText('No se pudo guardar el nuevo orden')).toBeVisible();
    // Restored: Claude Code 20x is the first row of its group again.
    const firstRow = page.locator('[data-testid^="accounting-row-"]').first();
    await expect(firstRow).toHaveAttribute('data-testid', 'accounting-row-1');
  });

  test('the categories modal lists the catalog with its usage count', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (subnav navigation into Recurrentes is
    // covered by the display specs above; this one pins behavior inside
    // the tab)
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recurring-manage-categories'))
      .toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-manage-categories').click();

    const modal = page.getByRole('dialog');
    await expect(
      modal.getByRole('heading', { name: 'Categorías de recurrentes' }),
    ).toBeVisible();
    await expect(modal.getByTestId('recurring-category-row-1')).toContainText('2 pagos');
    await expect(modal.getByTestId('recurring-category-row-2')).toContainText('1 pago');
  });

  test('deleting a category still in use is refused with the reason', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('recurring-manage-categories'))
      .toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-manage-categories').click();
    await page.getByTestId('recurring-category-delete-1').click();

    // Confirm the destructive action, then the backend refuses it.
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(page.getByText('No se pudo eliminar la categoría')).toBeVisible();
    await expect(
      page.getByText('Muévelos a otra categoría antes de borrarla', { exact: false }),
    ).toBeVisible();
    expect(calls.some((c) => c.apiPath.endsWith('/delete/'))).toBe(true);
  });

  test('cop_equivalent field only appears for USD payments in the modal', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Pagos recurrentes', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-new-button').click();
    await expect(
      page.getByRole('heading', { name: 'Nuevo pago recurrente' }),
    ).toBeVisible();

    // COP by default: no COP-equivalent field.
    await expect(page.getByText('Equivalente COP')).toHaveCount(0);

    await page.getByRole('tab', { name: 'USD' }).click();
    await expect(page.getByText('Equivalente COP')).toBeVisible();
  });

  test('creates a recurring payment through the modal', {
    tag: [...ADMIN_ACCOUNTING_RECURRING, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await page.goto('/panel/accounting/recurring', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Pagos recurrentes', exact: true }),
    ).toBeVisible({ timeout: 25_000 });

    await page.getByTestId('recurring-new-button').click();
    await page.locator('form input[type="text"]').first().fill('Netflix');
    await page.locator('form input[inputmode="numeric"]').first().fill('39800');
    await page.getByTestId('recurring-payment-form-submit').click();

    await expect(page.getByText('Pago recurrente creado')).toBeVisible();
    expect(calls).toHaveLength(1);
    expect(calls[0].body.name).toBe('Netflix');
  });
});
