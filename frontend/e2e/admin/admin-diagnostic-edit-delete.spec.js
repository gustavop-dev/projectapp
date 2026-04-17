/**
 * E2E tests for admin Web App Diagnostics — edit page render (admin-diagnostic-edit)
 * and delete flow from the list page (admin-diagnostic-delete).
 *
 * Covers: edit page renders 10 tabs and Resumen read-only data; list page 3-dot
 * menu opens, Eliminar triggers ConfirmModal, and DELETE API is called on confirm.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_DIAGNOSTIC_EDIT,
  ADMIN_DIAGNOSTIC_DELETE,
} from '../helpers/flow-tags.js';

const DIAG_ID = 55;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildDiagnostic(overrides = {}) {
  return {
    id: DIAG_ID,
    uuid: 'diag-edit-delete-uuid-5555',
    title: 'Diagnóstico — AcmeCorp',
    status: 'draft',
    language: 'es',
    client: { name: 'AcmeCorp', email: 'acme@example.com' },
    client_name: 'AcmeCorp',
    investment_amount: null,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 3,
    last_viewed_at: null,
    documents: [],
    attachments: [],
    public_url: `/diagnostic/diag-edit-delete-uuid-5555`,
    ...overrides,
  };
}

// ── Edit page ─────────────────────────────────────────────────────────────────

test.describe('Admin Diagnostic — Edit page', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9200, role: 'admin', is_staff: true },
    });
  });

  test('edit page renders all 6 navigation tabs', {
    tag: [...ADMIN_DIAGNOSTIC_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await expect(page.getByRole('button', { name: 'General', exact: true })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: 'Secciones' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Det. técnico' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Prompt Diagnostic' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'JSON' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Actividad' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Analytics' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Correos' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Documentos' })).toBeVisible();
  });

  test('General tab shows client name and language', {
    tag: [...ADMIN_DIAGNOSTIC_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    await page.getByRole('button', { name: 'General', exact: true }).click();

    await expect(page.locator('section').getByText('AcmeCorp')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('section').getByText('Español')).toBeVisible();
  });

  test('PATCH to update/ is called when General form is saved', {
    tag: [...ADMIN_DIAGNOSTIC_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let patchCalled = false;

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/update/` && method === 'PATCH') {
        patchCalled = true;
        return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
      }
      return null;
    });

    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);

    // Pricing fields now live in the General tab; click "Guardar Cambios" there.
    await page.getByTestId('diagnostic-edit-submit').click();

    await expect(() => expect(patchCalled).toBe(true)).toPass({ timeout: 5000 });
  });
});

// ── Delete flow ───────────────────────────────────────────────────────────────

test.describe('Admin Diagnostic — Delete flow', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9200, role: 'admin', is_staff: true },
    });
  });

  test('3-dot button opens actions modal with Eliminar option', {
    tag: [...ADMIN_DIAGNOSTIC_DELETE, '@role:admin'],
  }, async ({ page }) => {
    const diagnostic = buildDiagnostic();

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === 'diagnostics/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([diagnostic]) };
      }
      return null;
    });

    await page.goto('/panel/diagnostics');
    await expect(page.locator(`[data-testid="diagnostic-row-${DIAG_ID}"]`)).toBeVisible({ timeout: 15000 });

    await page.locator(`[data-testid="diagnostic-row-${DIAG_ID}"]`).locator('td').last().locator('button').click();

    await expect(page.getByRole('button', { name: 'Eliminar' })).toBeVisible({ timeout: 5000 });
  });

  test('confirming delete calls DELETE and removes diagnostic from list', {
    tag: [...ADMIN_DIAGNOSTIC_DELETE, '@role:admin'],
  }, async ({ page }) => {
    const diagnostic = buildDiagnostic();
    let deleteCalled = false;
    let diagnostics = [diagnostic];

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return authOk;
      if (apiPath === 'diagnostics/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(diagnostics) };
      }
      if (apiPath === `diagnostics/${DIAG_ID}/delete/` && method === 'DELETE') {
        deleteCalled = true;
        diagnostics = [];
        return { status: 204, body: '' };
      }
      return null;
    });

    await page.goto('/panel/diagnostics');
    await expect(page.locator(`[data-testid="diagnostic-row-${DIAG_ID}"]`)).toBeVisible({ timeout: 15000 });

    // Open actions modal
    await page.locator(`[data-testid="diagnostic-row-${DIAG_ID}"]`).locator('td').last().locator('button').click();

    // Click Eliminar
    await page.getByRole('button', { name: 'Eliminar' }).click();

    // ConfirmModal: click the danger confirm button
    await page.getByRole('button', { name: 'Eliminar', exact: true }).last().click();

    await expect(() => expect(deleteCalled).toBe(true)).toPass({ timeout: 5000 });
    await expect(page.locator(`[data-testid="diagnostic-row-${DIAG_ID}"]`)).not.toBeVisible({ timeout: 5000 });
  });
});
