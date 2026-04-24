/**
 * E2E tests for admin Web App Diagnostics — JSON export tab.
 *
 * Covers the `admin-diagnostic-json-export` flow: admin navigates to the
 * JSON tab, sees a read-only textarea with the serialised diagnostic JSON,
 * and can use Copiar, Descargar, and Actualizar action buttons.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_JSON_EXPORT } from '../helpers/flow-tags.js';

const DIAG_ID = 82;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: 'diag-json-export-uuid-8200',
    title: 'Diagnóstico — Delta Inc',
    status: 'draft',
    language: 'es',
    client: { id: 77, name: 'Delta Inc', email: 'delta@example.co' },
    client_name: 'Delta Inc',
    investment_amount: 11000000,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 0,
    last_viewed_at: null,
    sections: [
      {
        id: 801,
        section_type: 'purpose',
        title: 'Propósito',
        order: 1,
        is_enabled: true,
        visibility: 'both',
        content_json: { paragraphs: ['Párrafo de prueba'] },
        updated_at: '2026-04-18T10:00:00Z',
      },
    ],
    attachments: [],
    confidentiality_params: null,
    public_url: `/diagnostic/diag-json-export-uuid-8200`,
    updated_at: '2026-04-18T10:00:00Z',
    ...overrides,
  };
}

function setupMock(page, { onDetail = null } = {}) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
      if (onDetail) return onDetail();
      return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
    }
    return null;
  });
}

test.describe('Admin Diagnostic — JSON export tab', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9200, role: 'admin', is_staff: true },
    });
  });

  test('JSON tab shows read-only textarea with serialised diagnostic', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_EXPORT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();

    // Section heading visible.
    await expect(page.getByText('JSON del diagnóstico')).toBeVisible({ timeout: 10_000 });

    // Read-only textarea contains the diagnostic title.
    const exportTextarea = page.locator('textarea[readonly]');
    await expect(exportTextarea).toBeVisible();
    await expect(exportTextarea).toHaveValue(/Diagnóstico — Delta Inc/);
  });

  test('action buttons Actualizar, Copiar, and Descargar are present', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_EXPORT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();

    await expect(page.getByText('JSON del diagnóstico')).toBeVisible({ timeout: 10_000 });

    await expect(page.getByRole('button', { name: /Actualizar/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Copiar/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Descargar/i })).toBeVisible();
  });

  test('Actualizar refetches the diagnostic detail and updates the textarea', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_EXPORT, '@role:admin'],
  }, async ({ page }) => {
    let callCount = 0;
    await setupMock(page, {
      onDetail: () => {
        callCount++;
        const title = callCount > 1 ? 'Diagnóstico — Delta Inc (Actualizado)' : 'Diagnóstico — Delta Inc';
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic({ title })) };
      },
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();
    await expect(page.getByText('JSON del diagnóstico')).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Actualizar/i }).click();

    await expect(page.locator('textarea[readonly]')).toHaveValue(/Delta Inc \(Actualizado\)/, { timeout: 5_000 });
  });
});
