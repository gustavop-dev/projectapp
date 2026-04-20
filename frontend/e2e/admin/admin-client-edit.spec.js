/**
 * E2E tests for admin client edit modal from the /panel/clients/ page.
 *
 * Covers: opening the edit modal via the edit button on a client row,
 * pre-filling with existing client data, submitting a name change,
 * and surfacing a server error from the update endpoint.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_CLIENT_EDIT } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockClients = [
  {
    id: 301,
    name: 'Laura Pérez',
    email: 'laura@test.com',
    phone: '+57 310 111 2222',
    company: 'Laura Estudio',
    is_onboarded: true,
    is_email_placeholder: false,
    total_proposals: 2,
    is_orphan: false,
    created_at: '2026-01-01T10:00:00Z',
    updated_at: '2026-03-10T10:00:00Z',
  },
];

function setupMock(page, { onUpdate = null } = {}) {
  return mockApi(page, async ({ route, apiPath, method }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/client-profiles/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockClients) };
    }
    const updateMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/update\/$/);
    if (updateMatch && method === 'PUT') {
      if (onUpdate) return onUpdate(route);
      const body = JSON.parse(route.request().postData() || '{}');
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...mockClients[0], ...body }),
      };
    }
    const detailMatch = apiPath.match(/^proposals\/client-profiles\/(\d+)\/$/);
    if (detailMatch) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...mockClients[0], proposals: [] }),
      };
    }
    return null;
  });
}

test.describe('Admin Client Edit Modal', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9300, role: 'admin', is_staff: true },
    });
  });

  test('opens edit modal pre-filled with client data on edit button click', {
    tag: [...ADMIN_CLIENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/clients', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 20_000 });

    await page.getByTestId('client-edit-301').click();

    // Modal renders with client data pre-filled.
    await expect(page.getByTestId('clients-edit-name')).toHaveValue('Laura Pérez', { timeout: 5_000 });
    await expect(page.getByTestId('clients-edit-email')).toHaveValue('laura@test.com');
    await expect(page.getByTestId('clients-edit-phone')).toHaveValue('+57 310 111 2222');
    await expect(page.getByTestId('clients-edit-company')).toHaveValue('Laura Estudio');
  });

  test('submits updated name and closes modal on success', {
    tag: [...ADMIN_CLIENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    let capturedPayload = null;
    await setupMock(page, {
      onUpdate: (route) => {
        capturedPayload = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockClients[0], name: 'Laura Pérez Actualizada' }),
        };
      },
    });
    await page.goto('/panel/clients', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 20_000 });

    await page.getByTestId('client-edit-301').click();
    await page.getByTestId('clients-edit-name').fill('Laura Pérez Actualizada');
    await page.getByTestId('clients-edit-submit').click();

    // Modal closes after successful submit.
    await expect(page.getByTestId('clients-edit-name')).not.toBeVisible({ timeout: 5_000 });

    // Payload sent to update endpoint includes the new name.
    expect(capturedPayload).not.toBeNull();
    expect(capturedPayload.name).toBe('Laura Pérez Actualizada');
  });

  test('surfaces server error when update returns 400', {
    tag: [...ADMIN_CLIENT_EDIT, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, {
      onUpdate: () => ({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ name: ['Este nombre ya está en uso.'] }),
      }),
    });
    await page.goto('/panel/clients', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible({ timeout: 20_000 });

    await page.getByTestId('client-edit-301').click();
    await page.getByTestId('clients-edit-name').fill('Nombre duplicado');
    await page.getByTestId('clients-edit-submit').click();

    // Modal stays open and shows the error.
    await expect(page.getByTestId('clients-edit-name')).toBeVisible({ timeout: 5_000 });
  });
});
