/**
 * E2E tests for the Cuentas de cobro center at /panel/accounting/collections.
 *
 * FLOWS: admin-accounting-collections, admin-accounting-collection-create
 * Covers: status counters from list meta, the segmented Vencidas filter with
 *         the is_overdue badge, mark-paid and cancel behind ConfirmModal,
 *         resend to the client, the create modal with its mandatory income
 *         link and email/PDF preview step, and the Liquidar routing when
 *         marking an expected-linked cuenta as paid.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_ACCOUNTING_COLLECTIONS,
  ADMIN_ACCOUNTING_COLLECTION_CREATE,
  ADMIN_ACCOUNTING_COLLECTION_DETAIL,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

function makeRows() {
  return [
    {
      id: 1,
      public_number: 'PA-2026-0001',
      origin: 'hosting',
      origin_label: 'Hosting',
      // The snapshot the PDF printed: person and brand fused, which is the
      // defect the two columns below exist to separate.
      customer_name: 'German - Kore',
      client: 101,
      client_display_name: 'Germán Franco',
      project_name: 'Kore',
      total: '550002.00',
      issue_date: '2026-06-01',
      due_date: '2026-06-15',
      commercial_status: 'issued',
      commercial_status_label: 'Emitida',
      is_overdue: true,
    },
    {
      id: 2,
      public_number: 'PA-2026-0002',
      origin: 'hosting',
      origin_label: 'Hosting',
      // The snapshot the PDF printed: person and brand fused, which is the
      // defect the two columns below exist to separate.
      customer_name: 'Nestor - Xpandia',
      client: 102,
      client_display_name: 'Néstor Franco',
      project_name: 'Xpandia',
      total: '550002.00',
      issue_date: '2026-07-10',
      due_date: '2026-07-30',
      commercial_status: 'issued',
      commercial_status_label: 'Emitida',
      is_overdue: false,
    },
    {
      id: 3,
      public_number: 'PA-2026-0003',
      origin: 'hosting',
      origin_label: 'Hosting',
      // The snapshot the PDF printed: person and brand fused, which is the
      // defect the two columns below exist to separate.
      customer_name: 'Laura - Mi Huella',
      client: 103,
      client_display_name: 'Laura Gómez',
      project_name: 'Mi Huella',
      total: '550002.00',
      issue_date: '2026-05-01',
      due_date: '2026-05-15',
      commercial_status: 'paid',
      commercial_status_label: 'Pagada',
      is_overdue: false,
    },
  ];
}

const META = {
  issued_count: 2,
  issued_total: '1100004.00',
  paid_count: 1,
  paid_total: '550002.00',
  cancelled_count: 0,
};

const CLIENT_SEARCH_RESULT = [{
  id: 5,
  name: 'Ana Pérez',
  email: 'ana@acme.co',
  phone: '',
  company: 'Acme Soluciones',
  nit: '901234567',
  cedula: '',
  is_email_placeholder: false,
}];

const ELIGIBLE_INCOME = {
  id: 8,
  concept: 'Desarrollo módulo de reportes',
  kind: 'expected',
  kind_label: 'Esperado',
  payment_status: 'pending',
  total_amount: '1490000.00',
  pending_amount: '1490000.00',
  has_collection_account: false,
  collection_account_id: null,
  collection_account_number: null,
};

/** Rows where #2 carries an income link, so the detail modal has a history.
 *  Overridden locally rather than in makeRows(): the plain mark-paid test
 *  depends on the base rows NOT routing through Liquidar. */
async function mockWithLinkedIncome(page, calls = []) {
  const handler = buildHandler({ calls });
  await mockApi(page, async (ctx) => {
    if (ctx.apiPath === 'accounting/collection-accounts/' && ctx.method === 'GET') {
      const rows = makeRows();
      rows[1].income_record_id = 8;
      rows[1].income_kind = 'expected';
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: rows, meta: META }),
      };
    }
    return handler(ctx);
  });
}

function buildHandler({ calls, incomeDetail = null }) {
  const state = { rows: makeRows() };
  return async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath.startsWith('proposals/client-profiles/search/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(CLIENT_SEARCH_RESULT),
      };
    }
    if (/^accounting\/collection-accounts\/\d+\/$/.test(apiPath) && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          items: [{
            id: 1,
            description: 'Servicio de hosting kore.com.co',
            period_start: '2026-06-01',
            period_end: '2026-08-31',
            line_total: '550002.00',
          }],
          payment_methods: [],
          notes: '',
        }),
      };
    }
    // Must precede the incomes catch-all below, which would otherwise answer
    // /detail/ with the LIST shape.
    if (/^accounting\/incomes\/\d+\/detail\/$/.test(apiPath) && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          income: {
            ...ELIGIBLE_INCOME,
            concept: 'Hosting: Trimestral',
            period_label: 'Agosto 2026',
            gustavo_amount: '116640.00',
            carlos_amount: '116640.00',
            company_amount: '0.00',
          },
          liquid: [{
            id: 51, concept: 'Abono 1',
            total_amount: '88000.00', period_date: '2026-08-05',
          }],
          expenses: [{
            id: 61, concept: 'Comisión pasarela',
            total_amount: '12000.00', period_date: '2026-08-06',
            deduction_type_label: 'Comisión de pasarela',
          }],
          collection_account: null,
        }),
      };
    }
    if (/^accounting\/incomes\/\d+\/$/.test(apiPath) && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(incomeDetail || ELIGIBLE_INCOME),
      };
    }
    if (apiPath.startsWith('accounting/incomes/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [ELIGIBLE_INCOME], meta: {} }),
      };
    }
    if (apiPath.startsWith('accounting/collection-accounts/next-number/')) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          suggested_number: 'PA-ACME-001',
          billing_code: 'ACME',
          issuer_city: 'Bogotá',
        }),
      };
    }
    if (apiPath === 'accounting/collection-accounts/preview/' && method === 'POST') {
      calls.push({ apiPath, method, body: route.request().postDataJSON() });
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          subject: 'Cuenta de cobro PA-ACME-001 — ProjectApp',
          html_body: '<p>Valor a pagar: $1\'490.000 COP</p>',
          public_number: 'PA-ACME-001',
          total: '1490000.00',
          due_date: '2026-08-13',
          customer_email: 'ana@acme.co',
          pdf_base64: 'JVBERi0xLjQK',
        }),
      };
    }
    if (apiPath === 'accounting/collection-accounts/create/' && method === 'POST') {
      calls.push({ apiPath, method, body: route.request().postDataJSON() });
      const created = {
        id: 9,
        public_number: 'PA-ACME-001',
        origin: 'income',
        origin_label: 'Ingreso',
        customer_name: 'Acme Soluciones',
        client: 110,
        client_display_name: 'Ana Pérez',
        project_name: '',
        total: '1490000.00',
        issue_date: '2026-08-05',
        due_date: '2026-08-13',
        commercial_status: 'issued',
        commercial_status_label: 'Emitida',
        is_overdue: false,
        income_record_id: 8,
        income_kind: 'expected',
      };
      state.rows = [created, ...state.rows];
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ document: created, email_sent: true }),
      };
    }
    if (apiPath.startsWith('accounting/collection-accounts/') && method === 'POST') {
      const match = apiPath.match(
        /^accounting\/collection-accounts\/(\d+)\/(mark-paid|cancel|resend)\/$/,
      );
      if (match) {
        const [, id, action] = match;
        calls.push({ apiPath, method });
        const row = state.rows.find((item) => item.id === Number(id));
        if (action === 'mark-paid') {
          Object.assign(row, {
            commercial_status: 'paid',
            commercial_status_label: 'Pagada',
            is_overdue: false,
          });
        }
        if (action === 'cancel') {
          Object.assign(row, {
            commercial_status: 'cancelled',
            commercial_status_label: 'Anulada',
            is_overdue: false,
          });
        }
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(row),
        };
      }
    }
    if (apiPath.startsWith('accounting/collection-accounts/') && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: state.rows, meta: META }),
      };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

async function gotoCollections(page) {
  await page.goto('/panel/accounting/collections', { waitUntil: 'domcontentloaded' });
  await expect(
    page.getByRole('heading', { name: 'Cuentas de cobro', exact: true }),
  ).toBeVisible({ timeout: 25_000 });
  await expect(page.getByTestId('accounting-row-1')).toBeVisible();
}

test.describe('Admin Accounting Collections', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('the status counters combine list meta and overdue rows', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoCollections(page);

    await expect(page.getByTestId('accounting-stat-value')).toHaveText([
      '2', '1', '1', '0',
    ]);
    await expect(page.getByText('Por cobrar: $1.100.004')).toBeVisible();
    await expect(page.getByText('Recaudado: $550.002')).toBeVisible();
  });

  test('the Vencidas filter keeps only overdue rows with their badge', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoCollections(page);

    await page.getByRole('tab', { name: 'Vencidas' }).click();

    await expect(page.getByTestId('accounting-row-1')).toBeVisible();
    await expect(page.getByTestId('accounting-row-2')).toHaveCount(0);
    await expect(
      page.getByTestId('accounting-row-1').getByText('Vencida', { exact: true }),
    ).toBeVisible();
  });

  test('marking an issued account as paid confirms and updates the badge', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('accounting-row-2').getByLabel('Marcar pagada').click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(
      page.getByTestId('accounting-row-2').getByText('Pagada', { exact: true }),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/collection-accounts/2/mark-paid/',
      method: 'POST',
    });
  });

  test('cancelling an issued account confirms and shows Anulada', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('accounting-row-2').getByLabel('Anular').click();
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(
      page.getByTestId('accounting-row-2').getByText('Anulada', { exact: true }),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/collection-accounts/2/cancel/',
      method: 'POST',
    });
  });

  test('resending a paid account asks for confirmation naming the recipient', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('accounting-row-3').getByLabel('Reenviar al cliente').click();

    // One click used to email a client outright. It now confirms first, and
    // the message says who is about to receive it.
    await expect(page.getByText('Reenviar cuenta de cobro')).toBeVisible();
    await page.getByRole('button', { name: 'Reenviar', exact: true }).click();

    await expect(
      page.getByText('Cuenta de cobro reenviada al cliente'),
    ).toBeVisible();
    expect(calls).toContainEqual({
      apiPath: 'accounting/collection-accounts/3/resend/',
      method: 'POST',
    });
  });

  test('a failed resend surfaces the server error to the operator', {
    tag: [...ADMIN_ACCOUNTING_COLLECTIONS, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const calls = [];
    const handler = buildHandler({ calls });
    await mockApi(page, async (ctx) => {
      if (/^accounting\/collection-accounts\/\d+\/resend\/$/.test(ctx.apiPath)) {
        return {
          status: 502,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'No se pudo enviar el correo; revisa los logs e inténtalo de nuevo.',
          }),
        };
      }
      return handler(ctx);
    });
    await gotoCollections(page);

    await page.getByTestId('accounting-row-3').getByLabel('Reenviar al cliente').click();
    await page.getByRole('button', { name: 'Reenviar', exact: true }).click();

    await expect(page.getByText('No se pudo reenviar')).toBeVisible();
    // The row keeps its state — nothing was mutated by the failed send.
    await expect(
      page.getByTestId('accounting-row-3').getByText('Pagada', { exact: true }),
    ).toBeVisible();
  });

  test('creating a cuenta walks through the email preview before sending', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_CREATE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('collection-create-button').click();

    // Client from the clients module → snapshot + suggested consecutivo.
    await page.getByTestId('collection-form-client').fill('Acme');
    await page.getByTestId('client-autocomplete-option-5').click();
    await expect(page.getByTestId('collection-form-number')).toHaveValue('PA-ACME-001');
    await expect(page.getByTestId('collection-form-customer-email')).toHaveValue('ana@acme.co');

    // Mandatory income link via the searchable combobox.
    await page.getByTestId('collection-form-income').click();
    await page.getByTestId('collection-form-income-option-8').click();
    await expect(page.getByTestId('collection-form-concept'))
      .toHaveValue('Desarrollo módulo de reportes');

    await page.getByTestId('collection-form-preview').click();

    // Step 2: the real email + PDF the client will receive.
    await expect(page.getByTestId('collection-preview-subject'))
      .toContainText('PA-ACME-001');
    await expect(page.getByTestId('collection-preview-email')).toBeVisible();
    await expect(page.getByTestId('collection-preview-open-pdf')).toBeVisible();
    // The viewer tab cannot name a blob: URL, so saving needs its own action.
    await expect(page.getByTestId('collection-preview-download-pdf')).toBeVisible();

    // Email and PDF reviewable at the same time, each scrolling on its own:
    // the modal panel must not add a scrollbar nesting inside theirs, and the
    // summary and the send button must be reachable without scrolling.
    await expect(page.getByTestId('collection-preview-pdf')).toBeVisible();
    await expect(page.getByTestId('collection-preview-split-handle')).toBeVisible();
    await expect(page.getByTestId('collection-preview-subject')).toBeInViewport();
    await expect(page.getByTestId('collection-form-confirm')).toBeInViewport();
    const panelOverflow = await page
      .locator('[role="dialog"] > div:nth-child(2)')
      .evaluate((el) => el.scrollHeight - el.clientHeight);
    expect(panelOverflow).toBeLessThanOrEqual(1);

    await page.getByTestId('collection-form-confirm').click();

    await expect(page.getByText('Cuenta de cobro enviada')).toBeVisible();
    await expect(page.getByTestId('accounting-row-9')).toBeVisible();
    const createCall = calls.find(
      (call) => call.apiPath === 'accounting/collection-accounts/create/',
    );
    expect(createCall.body.income_record_id).toBe(8);
    expect(createCall.body.client_profile_id).toBe(5);
    // Untouched suggestion → the payload lets the backend allocate.
    expect(createCall.body.public_number).toBeUndefined();
  });

  test('the preview swaps email and PDF behind tabs when the window is too narrow', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_CREATE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the tab is a subnav entry; the layout under
    // test lives in the create modal, which IS opened by clicking)
    //
    // Below 1024px two columns leave neither panel legible, so they collapse
    // into tabs. Only a real browser can prove it: jsdom has no layout.
    await page.setViewportSize({ width: 820, height: 900 });
    const calls = [];
    await mockApi(page, buildHandler({ calls }));
    await gotoCollections(page);

    await page.getByTestId('collection-create-button').click();
    await page.getByTestId('collection-form-client').fill('Acme');
    await page.getByTestId('client-autocomplete-option-5').click();
    await page.getByTestId('collection-form-income').click();
    await page.getByTestId('collection-form-income-option-8').click();
    await page.getByTestId('collection-form-preview').click();

    await expect(page.getByTestId('collection-preview-subject')).toBeVisible();
    // Stacked: no divider to drag, and the email leads on a tablet.
    await expect(page.getByTestId('collection-preview-split-handle')).toHaveCount(0);
    await expect(page.getByTestId('collection-preview-email')).toBeVisible();
    await expect(page.getByTestId('collection-preview-pdf')).toBeHidden();

    await page.getByTestId('collection-preview-tab-pdf').click();

    await expect(page.getByTestId('collection-preview-pdf')).toBeVisible();
    await expect(page.getByTestId('collection-preview-email')).toBeHidden();
    // Reviewing the document never costs the operator the send decision.
    await expect(page.getByTestId('collection-form-confirm')).toBeInViewport();
  });

  test('marking an expected-linked cuenta as paid opens the Liquidar modal', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_CREATE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the tab is a subnav entry; the routing under
    // test starts at the row's Marcar pagada action, which IS clicked)
    const calls = [];
    const handler = buildHandler({
      calls,
      incomeDetail: { ...ELIGIBLE_INCOME, payment_status: 'partial' },
    });
    await mockApi(page, async (ctx) => {
      if (ctx.apiPath === 'accounting/collection-accounts/' && ctx.method === 'GET') {
        const rows = makeRows();
        rows[1].income_record_id = 8;
        rows[1].income_kind = 'expected';
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ results: rows, meta: META }),
        };
      }
      return handler(ctx);
    });
    await gotoCollections(page);

    await page.getByTestId('accounting-row-2').getByLabel('Marcar pagada').click();

    // Never a silent mark-paid: the Liquidar modal takes over.
    await expect(
      page.getByRole('heading', { name: 'Liquidar ingreso esperado' }),
    ).toBeVisible();
    await expect(page.getByTestId('confirm-modal-confirm')).toBeHidden();
    expect(calls.some(
      (call) => call.apiPath.endsWith('/mark-paid/'),
    )).toBe(false);
  });

  test('Cliente and Proyecto are separate columns, each sortable on its own', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_DETAIL, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the tab is a subnav entry; the behaviour under
    // test is the column sort, which IS clicked below)
    await mockApi(page, buildHandler({ calls: [] }));
    await gotoCollections(page);

    // The fixture carries the old `Persona - Marca` snapshot in
    // customer_name; the columns must show the two halves apart.
    const row = page.getByTestId('accounting-row-1');
    await expect(row).toContainText('Germán Franco');
    await expect(row).toContainText('Kore');

    // Sorting by Proyecto alone is what "filtrables y ordenables por
    // separado" actually means — a shared column could not do this.
    await page.getByTestId('accounting-sort-project_name').click();

    const projects = page.locator('[data-testid^="accounting-row-"]');
    await expect(projects.first()).toContainText('Kore');
    await expect(projects.last()).toContainText('Xpandia');
  });

  test('opening the detail shows the linked income and its settlement history', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_DETAIL, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the tab is a subnav entry; the behaviour under
    // test is the detail modal, which IS opened by clicking the row action)
    await mockWithLinkedIncome(page);
    await gotoCollections(page);

    await page.getByTestId('collection-view-detail-2').click();

    const modal = page.getByTestId('collection-detail-modal');
    await expect(modal).toBeVisible();
    await expect(page.getByTestId('collection-detail-client'))
      .toHaveText('Néstor Franco');
    await expect(page.getByTestId('collection-detail-project'))
      .toHaveText('Xpandia');
    // The history the panel could not reach before this branch.
    await expect(
      page.getByTestId('collection-detail-settlement-row'),
    ).toHaveCount(2);
    await expect(modal).toContainText('Abono 1');
    await expect(modal).toContainText('Comisión de pasarela');
  });

  test('the Documento tab embeds the PDF instead of downloading it', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_DETAIL, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the tab is a subnav entry; the behaviour under
    // test is the Documento tab, reached by clicking the row action then the tab)
    await mockWithLinkedIncome(page);
    await gotoCollections(page);

    await page.getByTestId('collection-view-detail-2').click();
    await page.getByRole('tab', { name: 'Documento' }).click();

    await expect(page.getByTestId('collection-detail-pdf')).toHaveAttribute(
      'src', '/api/accounting/collection-accounts/2/pdf/?inline=1',
    );
  });

  test('going to the income lands on a tab that does not filter it out', {
    tag: [...ADMIN_ACCOUNTING_COLLECTION_DETAIL, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the tab is a subnav entry; the behaviour under
    // test is the exit link inside the modal, which IS clicked)
    await mockWithLinkedIncome(page);
    await gotoCollections(page);

    await page.getByTestId('collection-view-detail-2').click();
    await page.getByTestId('collection-detail-go-to-income').click();

    // Without the tab param Ingresos lands on its "Solo esperados" builtin,
    // which filters the focused row straight out of its own list.
    await expect(page).toHaveURL(/accounting_incomeTab=all/);
    await expect(page).toHaveURL(/focus=8/);
  });
});
