/**
 * E2E tests for admin Web App Diagnostics — NDA Edit Params.
 *
 * Covers the `admin-diagnostic-confidentiality-edit` flow: admin opens
 * the Documentos tab on a diagnostic with an existing generated NDA,
 * clicks "Editar parámetros", verifies the modal pre-fills from saved
 * confidentiality_params, modifies a field, submits, and the modal closes.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_CONFIDENTIALITY_EDIT } from '../helpers/flow-tags.js';

const DIAG_ID = 78;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const savedParams = {
  client_full_name: 'Beta Corp SAS',
  client_cedula: '800.555.111-2',
  client_legal_representative: 'Juan Gómez',
  client_email: 'juan@betacorp.co',
  contractor_full_name: 'Project App SAS',
  contractor_cedula: '900.123.456-7',
  contractor_email: 'team@projectapp.co',
  contract_city: 'Medellín',
  contract_day: '5',
  contract_month: 'abril',
  contract_year: '2026',
  penal_clause_value: 'CINCUENTA SALARIOS MÍNIMOS MENSUALES LEGALES VIGENTES (50 SMMLV)',
};

const ndaAttachment = {
  id: 601,
  document_type: 'confidentiality_agreement',
  document_type_display: 'Acuerdo de Confidencialidad',
  title: 'Acuerdo de Confidencialidad',
  file: '/media/diagnostics/78/nda.pdf',
  is_generated: true,
  created_at: '2026-04-15T10:00:00Z',
};

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: 'diag-nda-edit-uuid-7800',
    title: 'Diagnóstico — Beta Corp',
    status: 'negotiating',
    language: 'es',
    client: { id: 55, name: 'Beta Corp', email: 'contact@betacorp.co' },
    client_name: 'Beta Corp',
    investment_amount: 7000000,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 2,
    last_viewed_at: null,
    sections: [],
    attachments: [ndaAttachment],
    confidentiality_params: savedParams,
    public_url: `/diagnostic/diag-nda-edit-uuid-7800`,
    ...overrides,
  };
}

function setupMock(page, { onPost = null } = {}) {
  return mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/email/defaults/`) {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/email/history/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], total: 0, page: 1, has_next: false }) };
    }
    if (apiPath === `diagnostics/${DIAG_ID}/confidentiality/params/` && method === 'POST') {
      if (onPost) return onPost(route);
      const body = route.request().postDataJSON();
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ confidentiality_params: body.confidentiality_params, attachment: ndaAttachment }) };
    }
    return null;
  });
}

const modalRoot = (page) => page.locator('div.z-\\[9999\\]').filter({
  has: page.getByRole('heading', { level: 2 }),
});

test.describe('Admin Diagnostic — Edit NDA Params', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9200, role: 'admin', is_staff: true },
    });
  });

  test('opens modal pre-filled with saved confidentiality_params on "Editar parámetros" click', {
    tag: [...ADMIN_DIAGNOSTIC_CONFIDENTIALITY_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Documentos' }).click();
    await expect(page.getByRole('button', { name: /Editar parámetros/i })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Editar parámetros/i }).click();

    const modal = modalRoot(page);
    await expect(modal.locator('h2', { hasText: 'Acuerdo de Confidencialidad' })).toBeVisible({ timeout: 5_000 });

    // Client block pre-filled.
    const clientName = modal.locator('label').filter({ hasText: 'Razón social / Nombre' }).first().locator('input');
    await expect(clientName).toHaveValue('Beta Corp SAS');

    const clientCedula = modal.locator('label').filter({ hasText: 'NIT / C.C.' }).first().locator('input');
    await expect(clientCedula).toHaveValue('800.555.111-2');
  });

  test('submits modified field and closes modal on success', {
    tag: [...ADMIN_DIAGNOSTIC_CONFIDENTIALITY_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;
    await setupMock(page, {
      onPost: (route) => {
        capturedPayload = route.request().postDataJSON();
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ confidentiality_params: capturedPayload.confidentiality_params, attachment: ndaAttachment }) };
      },
    });
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Documentos' }).click();
    await expect(page.getByRole('button', { name: /Editar parámetros/i })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Editar parámetros/i }).click();

    const modal = modalRoot(page);
    await expect(modal.locator('h2', { hasText: 'Acuerdo de Confidencialidad' })).toBeVisible();

    const clientName = modal.locator('label').filter({ hasText: 'Razón social / Nombre' }).first().locator('input');
    await clientName.fill('Beta Corp SAS (Actualizado)');

    await page.getByRole('button', { name: 'Guardar y generar PDF' }).click();

    // Modal closes after success.
    await expect(modal).toBeHidden({ timeout: 10_000 });

    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.confidentiality_params.client_full_name).toBe('Beta Corp SAS (Actualizado)');
  });

  test('surfaces server error when POST returns 400 and keeps modal open', {
    tag: [...ADMIN_DIAGNOSTIC_CONFIDENTIALITY_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, {
      onPost: () => ({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Datos inválidos.' }),
      }),
    });
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Documentos' }).click();
    await expect(page.getByRole('button', { name: /Editar parámetros/i })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Editar parámetros/i }).click();

    const modal = modalRoot(page);
    await expect(modal.locator('h2', { hasText: 'Acuerdo de Confidencialidad' })).toBeVisible();

    await page.getByRole('button', { name: 'Guardar y generar PDF' }).click();

    await expect(modal).toBeVisible({ timeout: 5_000 });
    await expect(page.getByText('Datos inválidos.')).toBeVisible();
  });
});
