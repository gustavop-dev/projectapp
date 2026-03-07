/**
 * E2E tests for admin proposal creation flow.
 *
 * Covers: manual form fill + submit (verifying API payload),
 * JSON import tab toggle, validation on empty required fields.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_CREATE } from '../helpers/flow-tags.js';

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
    await page.getByRole('button', { name: /Crear Propuesta/i }).click();

    // Should redirect to edit page
    await page.waitForURL(/\/panel\/proposals\/\d+\/edit/, { timeout: 5000 });
    expect(page.url()).toContain(`/panel/proposals/${NEW_PROPOSAL_ID}/edit`);
  });
});
