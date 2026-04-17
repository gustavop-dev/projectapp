/**
 * E2E tests for admin Web App Diagnostic — JSON tab (import branch).
 *
 * Covers: paste valid JSON → preview renders; click "Aplicar JSON" issues
 * PATCH /update/ + POST /sections/bulk-update/; invalid JSON blocks apply.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_JSON_IMPORT } from '../helpers/flow-tags.js';

const DIAG_ID = 21;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: 'diag-json-import-uuid',
    title: 'Diagnóstico original',
    status: 'draft',
    language: 'es',
    client: { id: 1, name: 'AcmeCorp', email: 'acme@example.com' },
    client_name: 'AcmeCorp',
    investment_amount: 1000000,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 0,
    last_viewed_at: null,
    sections: [
      { id: 501, section_type: 'purpose', title: 'Propósito', order: 1, is_enabled: true, visibility: 'both', content_json: {} },
    ],
    attachments: [],
    public_url: '/diagnostic/diag-json-import-uuid',
    ...overrides,
  };
}

const importPayload = {
  metadata: {
    title: 'Diagnóstico importado',
    language: 'es',
    investment_amount: 2500000,
    currency: 'USD',
    client: { id: 77, name: 'Globex S.A.', email: 'globex@example.com' },
  },
  sections: [
    { id: 501, section_type: 'purpose', title: 'Propósito (importado)', order: 1, is_enabled: true, visibility: 'both', content_json: { paragraphs: ['Nuevo texto'] } },
    { id: 502, section_type: 'scope', title: 'Alcance', order: 2, is_enabled: true, visibility: 'final', content_json: { considerations: ['Item A'] } },
  ],
};

test.describe('Admin Diagnostic — JSON tab (import)', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9100, role: 'admin', is_staff: true },
    });
  });

  test('pasting valid JSON renders the preview card and enables Aplicar', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_IMPORT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();

    const textarea = page.getByPlaceholder(/Pega aquí el JSON completo/i);
    await textarea.fill(JSON.stringify(importPayload));

    await expect(page.getByText('Globex S.A.', { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('2', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /Aplicar JSON/i })).toBeEnabled();
  });

  test('invalid JSON shows an error message and hides the Aplicar button', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_IMPORT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();

    const textarea = page.getByPlaceholder(/Pega aquí el JSON completo/i);
    await textarea.fill('{ not valid json');

    await expect(page.getByText(/JSON inválido/)).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /Aplicar JSON/i })).toHaveCount(0);
  });

  test('clicking "Aplicar JSON" issues PATCH /update/ and POST /sections/bulk-update/', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_IMPORT, '@role:admin'],
  }, async ({ page }) => {
    let updateBody = null;
    let bulkBody = null;

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/update/` && method === 'PATCH') {
        updateBody = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(buildDiagnostic({
            title: 'Diagnóstico importado',
            investment_amount: 2500000,
            currency: 'USD',
          })),
        };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/sections/bulk-update/` && method === 'POST') {
        bulkBody = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(buildDiagnostic({ sections: importPayload.sections })),
        };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();

    const textarea = page.getByPlaceholder(/Pega aquí el JSON completo/i);
    await textarea.fill(JSON.stringify(importPayload));

    await page.getByRole('button', { name: /Aplicar JSON/i }).click();

    await expect(page.getByText('JSON aplicado correctamente.')).toBeVisible({ timeout: 10000 });

    expect(updateBody).toMatchObject({
      title: 'Diagnóstico importado',
      currency: 'USD',
      investment_amount: 2500000,
      client_id: 77,
    });
    expect(Array.isArray(bulkBody?.sections)).toBe(true);
    expect(bulkBody.sections).toHaveLength(2);
    expect(bulkBody.sections[0]).toMatchObject({ id: 501, title: 'Propósito (importado)' });
  });

  test('server error on bulk-update surfaces as inline error message', {
    tag: [...ADMIN_DIAGNOSTIC_JSON_IMPORT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/update/` && method === 'PATCH') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/sections/bulk-update/` && method === 'POST') {
        return { status: 400, contentType: 'application/json', body: JSON.stringify({ error: 'sections payload malformed' }) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('button', { name: 'JSON' }).click();

    await page.getByPlaceholder(/Pega aquí el JSON completo/i).fill(JSON.stringify(importPayload));
    await page.getByRole('button', { name: /Aplicar JSON/i }).click();

    await expect(page.getByText(/fallaron las secciones/i)).toBeVisible({ timeout: 10000 });
  });
});
