/**
 * E2E tests for admin Web App Diagnostics — Prompt editor tab.
 *
 * Covers the `admin-diagnostic-prompt` flow: admin navigates to the
 * Prompt tab, switches between commercial/technical sub-tabs, uses
 * the Editar/Copiar/Descargar .md buttons, edits and saves a custom
 * prompt, and restores the original default.
 *
 * All state is stored in localStorage — no API calls involved.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_DIAGNOSTIC_PROMPT } from '../helpers/flow-tags.js';

const DIAG_ID = 83;

const authOk = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function buildDiagnostic() {
  return {
    id: DIAG_ID,
    uuid: 'diag-prompt-uuid-8300',
    title: 'Diagnóstico — Epsilon Corp',
    status: 'draft',
    language: 'es',
    client: { id: 88, name: 'Epsilon Corp', email: 'epsilon@example.co' },
    client_name: 'Epsilon Corp',
    investment_amount: 5000000,
    currency: 'COP',
    payment_terms: {},
    duration_label: '',
    size_category: '',
    radiography: {},
    view_count: 0,
    last_viewed_at: null,
    sections: [],
    attachments: [],
    confidentiality_params: null,
    public_url: `/diagnostic/diag-prompt-uuid-8300`,
  };
}

function setupMock(page) {
  return mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authOk;
    if (apiPath === `diagnostics/${DIAG_ID}/detail/`) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(buildDiagnostic()) };
    }
    return null;
  });
}

test.describe('Admin Diagnostic — Prompt editor tab', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9200, role: 'admin', is_staff: true },
    });
    // Clear any previously saved custom prompts so each test starts with defaults.
    await page.addInitScript(() => {
      localStorage.removeItem('projectapp-diagnostic-commercial-prompt');
      localStorage.removeItem('projectapp-diagnostic-technical-prompt');
    });
  });

  test('Prompt tab shows commercial/technical sub-tabs with action buttons', {
    tag: [...ADMIN_DIAGNOSTIC_PROMPT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Prompt' }).click();

    // Commercial sub-tab active by default.
    await expect(page.getByRole('button', { name: /Propuesta comercial/i })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('button', { name: /Detalle técnico/i })).toBeVisible();

    // Action buttons for the default (view) state.
    await expect(page.getByRole('button', { name: /Editar/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Copiar/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Descargar \.md/i }).first()).toBeVisible();

    // "Restaurar original" only appears after customisation — should be absent.
    await expect(page.getByRole('button', { name: /Restaurar original/i })).not.toBeVisible();
  });

  test('Editar switches to edit mode with Guardar/Cancelar buttons and editable textarea', {
    tag: [...ADMIN_DIAGNOSTIC_PROMPT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Prompt' }).click();
    await expect(page.getByRole('button', { name: /Editar/i }).first()).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Editar/i }).first().click();

    await expect(page.getByRole('button', { name: /Guardar/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Cancelar/i })).toBeVisible();
    await expect(page.locator('textarea').first()).toBeVisible();
  });

  test('saves a custom prompt and shows "Restaurar original" button', {
    tag: [...ADMIN_DIAGNOSTIC_PROMPT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Prompt' }).click();
    await expect(page.getByRole('button', { name: /Editar/i }).first()).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Editar/i }).first().click();

    const textarea = page.locator('textarea').first();
    await textarea.fill('Prompt personalizado de prueba.');
    await page.getByRole('button', { name: /Guardar/i }).click();

    // Back to view mode — custom text rendered.
    await expect(page.locator('pre').first()).toContainText('Prompt personalizado de prueba.', { timeout: 5_000 });

    // "Restaurar original" now visible.
    await expect(page.getByRole('button', { name: /Restaurar original/i })).toBeVisible();
  });

  test('Restaurar original reverts custom prompt and hides "Restaurar original"', {
    tag: [...ADMIN_DIAGNOSTIC_PROMPT, '@role:admin'],
  }, async ({ page }) => {
    // Seed a custom prompt via localStorage before navigation.
    await page.addInitScript(() => {
      localStorage.setItem('projectapp-diagnostic-commercial-prompt', 'Prompt personalizado de prueba.');
    });

    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Prompt' }).click();

    await expect(page.getByRole('button', { name: /Restaurar original/i })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Restaurar original/i }).click();

    // Default prompt restored — "Restaurar original" disappears.
    await expect(page.getByRole('button', { name: /Restaurar original/i })).not.toBeVisible({ timeout: 5_000 });
    await expect(page.locator('pre').first()).not.toContainText('Prompt personalizado de prueba.');
  });

  test('Detalle técnico sub-tab shows its own prompt editor', {
    tag: [...ADMIN_DIAGNOSTIC_PROMPT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto(`/panel/diagnostics/${DIAG_ID}/edit`);
    await page.getByRole('tab', { name: 'Prompt' }).click();
    await expect(page.getByRole('button', { name: /Detalle técnico/i })).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: /Detalle técnico/i }).click();

    await expect(page.getByRole('button', { name: /Editar/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Copiar/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Descargar \.md/i }).first()).toBeVisible();
  });
});
