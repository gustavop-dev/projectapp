/**
 * E2E tests for the accounting export buttons.
 *
 * FLOW: admin-accounting-export
 * Covers: per-list CSV export carrying the active filters as query
 *         params, and the full workbook download from the dashboard.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ACCOUNTING_EXPORT } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

const CSV_BODY = '﻿Concepto,Tipo\nKore - Inicio 40%,Líquido\n';

function buildHandler({ exportCalls }) {
  return async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: { username: 'admin', is_staff: true, is_superuser: true },
        }),
      };
    }
    if (apiPath === 'accounting/incomes/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [{
            id: 1,
            concept: 'Kore - Inicio 40%',
            kind: 'liquid',
            kind_label: 'Líquido',
            period: '2026-02',
            period_label: 'Febrero 2026',
            period_date: '2026-02-01',
            destination: 'partners',
            destination_label: 'Socios',
            ledger: 'company',
            ledger_label: 'Empresa',
            total_amount: '1160000.00',
            gustavo_amount: '580000.00',
            carlos_amount: '580000.00',
            company_amount: '0.00',
            expected_income: null,
            pocket_movement: null,
            notes: '',
            created_at: '2026-02-01T10:00:00Z',
            updated_at: '2026-02-01T10:00:00Z',
          }],
          meta: {},
        }),
      };
    }
    if (apiPath.startsWith('accounting/export/workbook/')) {
      exportCalls.push({ apiPath });
      return {
        status: 200,
        contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers: {
          'Content-Disposition': 'attachment; filename="contabilidad_projectapp_2026_20260703.xlsx"',
        },
        body: 'stub-xlsx',
      };
    }
    if (apiPath.startsWith('accounting/export/')) {
      const url = new URL(route.request().url());
      exportCalls.push({
        apiPath,
        params: Object.fromEntries(url.searchParams.entries()),
      });
      return {
        status: 200,
        contentType: 'text/csv; charset=utf-8',
        headers: {
          'Content-Disposition': 'attachment; filename="contabilidad_income_20260703.csv"',
        },
        body: CSV_BODY,
      };
    }
    if (apiPath === 'accounting/dashboard/') {
      return null;
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    return null;
  };
}

test.describe('Admin Accounting Export', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9001, role: 'admin', is_staff: true },
    });
  });

  test('exports the incomes CSV with the active filters as params', {
    tag: [...ADMIN_ACCOUNTING_EXPORT, '@role:admin'],
  }, async ({ page }) => {
    const exportCalls = [];
    await mockApi(page, buildHandler({ exportCalls }));
    await page.goto('/panel/accounting/incomes', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Ingresos' }),
    ).toBeVisible({ timeout: 25_000 });

    // Apply a filter so the export carries it.
    await page.getByRole('button', { name: /Filtros/ }).click();
    await page.getByRole('tab', { name: 'Líquido' }).click();

    const downloadPromise = page.waitForEvent('download');
    await page.getByTestId('accounting-export-button').click();
    await page.getByRole('menuitem', { name: 'CSV' }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/^contabilidad_income_.*\.csv$/);
    expect(exportCalls).toHaveLength(1);
    expect(exportCalls[0].params.section).toBe('income');
    expect(exportCalls[0].params.file_format).toBe('csv');
    expect(exportCalls[0].params.kind).toBe('liquid');
  });
});
