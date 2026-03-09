/**
 * E2E tests for admin proposal creation flow.
 *
 * Covers: manual form fill + submit (verifying API payload),
 * JSON import tab toggle, validation on empty required fields.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_CREATE, ADMIN_PROPOSAL_CREATE_FROM_JSON } from '../helpers/flow-tags.js';

const NEW_PROPOSAL_ID = 99;

const mockCreatedProposal = {
  id: NEW_PROPOSAL_ID,
  uuid: '99999999-9999-9999-9999-999999999999',
  title: 'Nueva Propuesta Web',
  client_name: 'Carlos López',
  client_email: 'carlos@test.com',
  status: 'draft',
  sections: [],
  requirement_groups: [],
};

test.describe('Admin Proposal Create', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders proposal creation form with Manual tab active by default', {
    tag: [...ADMIN_PROPOSAL_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      return null;
    });
    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Nueva Propuesta' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Manual' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Importar JSON' })).toBeVisible();
    // Title input visible in manual mode
    await expect(page.getByLabel('Título')).toBeVisible();
  });

  test('fills manual form and submits, verifying API payload', {
    tag: [...ADMIN_PROPOSAL_CREATE, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;

    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/create/') {
        capturedPayload = route.request().postDataJSON();
        return { status: 201, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
      }
      return null;
    });

    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    // Fill required fields
    await page.getByLabel('Título').fill('Nueva Propuesta Web');
    await page.getByLabel('Nombre del cliente').fill('Carlos López');
    await page.getByLabel('Email del cliente').fill('carlos@test.com');

    // Submit form — wait for the API response
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/create/')),
      page.getByRole('button', { name: /Crear Propuesta/i }).click(),
    ]);
    await response.finished();

    // Verify payload captured
    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.title).toBe('Nueva Propuesta Web');
    expect(capturedPayload.client_name).toBe('Carlos López');
    expect(capturedPayload.client_email).toBe('carlos@test.com');
  });

  test('switching to JSON import tab shows textarea', {
    tag: [...ADMIN_PROPOSAL_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      return null;
    });

    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    // Switch to JSON import tab
    await page.getByRole('button', { name: 'Importar JSON' }).click();

    // Manual form fields should be hidden
    await expect(page.getByLabel('Título')).not.toBeVisible();
  });

  test('successful creation redirects to the new proposal edit page', {
    tag: [...ADMIN_PROPOSAL_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      if (apiPath === 'proposals/create/') return { status: 201, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
      if (apiPath === `proposals/${NEW_PROPOSAL_ID}/detail/`) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
      return null;
    });

    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    await page.getByLabel('Título').fill('Nueva Propuesta Web');
    await page.getByLabel('Nombre del cliente').fill('Carlos López');
    await page.getByLabel('Email del cliente').fill('carlos@test.com');

    // Submit and wait for API response before expecting redirect
    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/create/')),
      page.getByRole('button', { name: /Crear Propuesta/i }).click(),
    ]);
    await response.finished();

    // Should redirect to edit page (auto-retrying assertion for SPA navigation)
    await expect(page).toHaveURL(/\/panel\/proposals\/\d+\/edit/, { timeout: 10000 });
  });

  test('selecting "Otro" project type shows custom text input', {
    tag: [...ADMIN_PROPOSAL_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      return null;
    });
    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    const customInput = page.getByPlaceholder('Especificar tipo de proyecto...');
    await expect(customInput).not.toBeVisible();

    await page.locator('select').filter({ hasText: 'Sin definir' }).first().selectOption('other');
    await expect(customInput).toBeVisible();
  });
});

test.describe('Admin Proposal Create from JSON', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  const validJson = JSON.stringify({
    general: { clientName: 'Ana Martínez' },
    executiveSummary: { paragraphs: ['Resumen ejecutivo.'] },
  });

  const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

  test('pasting valid JSON shows preview with client name and section count', {
    tag: [...ADMIN_PROPOSAL_CREATE_FROM_JSON, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const textarea = page.getByPlaceholder(/general/);
    await textarea.fill(validJson);
    await textarea.dispatchEvent('input');

    await expect(page.getByText('Ana Martínez')).toBeVisible();
    await expect(page.getByText('Datos de la propuesta')).toBeVisible();
  });

  test('pasting JSON without general key shows validation error', {
    tag: [...ADMIN_PROPOSAL_CREATE_FROM_JSON, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const textarea = page.getByPlaceholder(/general/);
    await textarea.fill(JSON.stringify({ executiveSummary: {} }));
    await textarea.dispatchEvent('input');

    await expect(page.getByText(/general.*clientName/i)).toBeVisible();
  });

  test('pasting invalid JSON shows syntax error', {
    tag: [...ADMIN_PROPOSAL_CREATE_FROM_JSON, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      return null;
    });
    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const textarea = page.getByPlaceholder(/general/);
    await textarea.fill('{ invalid json }');
    await textarea.dispatchEvent('input');

    await expect(page.getByText('JSON inválido')).toBeVisible();
  });

  test('submitting valid JSON creates proposal and redirects to edit page', {
    tag: [...ADMIN_PROPOSAL_CREATE_FROM_JSON, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;

    await mockApi(page, async ({ route, apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'proposals/create-from-json/') {
        capturedPayload = route.request().postDataJSON();
        return { status: 201, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
      }
      if (apiPath === `proposals/${NEW_PROPOSAL_ID}/detail/`) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockCreatedProposal) };
      }
      return null;
    });

    await page.goto('/panel/proposals/create');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'Importar JSON' }).click();
    const textarea = page.getByPlaceholder(/general/);
    await textarea.fill(validJson);
    await textarea.dispatchEvent('input');

    await expect(page.getByText('Datos de la propuesta')).toBeVisible();

    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/create-from-json/')),
      page.getByRole('button', { name: /Crear desde JSON/i }).click(),
    ]);
    await response.finished();

    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.client_name).toBe('Ana Martínez');
    expect(capturedPayload.sections).toBeDefined();
    expect(capturedPayload.sections.general).toBeDefined();

    await expect(page).toHaveURL(/\/panel\/proposals\/\d+\/edit/, { timeout: 10000 });
  });
});
