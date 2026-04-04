/**
 * E2E tests for platform project data model flow.
 *
 * @flow:platform-project-data-model
 * Covers: admin upload card visibility, JSON template buttons, entity table rendering,
 *         JSON validation errors, successful upload, client role access guard,
 *         and empty state for both roles.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_PROJECT_DATA_MODEL } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockProject = {
  id: 1, name: 'E-commerce Platform', status: 'active', progress: 33,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp', start_date: '2025-01-01', estimated_end_date: '2025-06-30',
};

const mockEntities = [
  {
    id: 1, name: 'User', description: 'Platform user account',
    key_fields: 'id, email, role', relationship: 'has many Orders',
  },
  {
    id: 2, name: 'Order', description: 'Purchase transaction',
    key_fields: 'id, total, status', relationship: 'belongs to User',
  },
];

const mockTemplate = {
  entities: [
    { name: 'ExampleEntity', description: 'Description', keyFields: 'id, name', relationship: 'belongs to X' },
  ],
};

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });

function setupMocks(page, { user, entities = mockEntities } = {}) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/1/data-model-entities/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(entities) };
    }
    if (apiPath === 'accounts/projects/1/data-model-entities/' && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockEntities) };
    }
    if (apiPath === 'accounts/projects/1/data-model-entities/template/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockTemplate) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

// ─── Admin role ────────────────────────────────────────────────────────────────

test.describe('Platform Data Model — Admin', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders upload card with template buttons', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await expect(page.getByRole('button', { name: /copiar plantilla/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /descargar plantilla/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /subir modelo de datos/i })).toBeVisible();
  });

  test('renders entity table with rows loaded from API', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await expect(page.getByRole('cell', { name: 'User', exact: true })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Order' })).toBeVisible();
    await expect(page.getByText('Platform user account')).toBeVisible();
    await expect(page.getByText('has many Orders')).toBeVisible();
  });

  test('shows parse error when JSON has no entities key', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await page.getByPlaceholder(/entities/i).fill('{"wrong": []}');
    await expect(page.getByText(/debe contener una clave.*entities/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /subir modelo de datos/i })).toBeDisabled();
  });

  test('shows parse error when JSON is syntactically invalid', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await page.getByPlaceholder(/entities/i).fill('{not valid json}');
    await expect(page.getByText(/JSON invalido/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /subir modelo de datos/i })).toBeDisabled();
  });

  test('shows entity count preview and enables submit for valid JSON', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    const validJson = JSON.stringify({ entities: [{ name: 'Product', description: 'A product', keyFields: 'id', relationship: '' }] });
    await page.getByPlaceholder(/entities/i).fill(validJson);

    await expect(page.getByText(/1 entidad/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /subir modelo de datos/i })).toBeEnabled();
  });

  test('uploads valid JSON and shows success banner', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    const validJson = JSON.stringify({ entities: [{ name: 'Product', description: 'A product', keyFields: 'id', relationship: '' }] });
    await page.getByPlaceholder(/entities/i).fill(validJson);
    await expect(page.getByRole('button', { name: /subir modelo de datos/i })).toBeEnabled();

    const uploadResponse = page.waitForResponse(
      (res) => res.url().includes('data-model-entities/') && res.request().method() === 'POST',
    );
    await page.getByRole('button', { name: /subir modelo de datos/i }).click();
    await uploadResponse;

    await expect(page.getByText(/modelo de datos actualizado correctamente/i)).toBeVisible();
  });

  test('shows empty state with admin hint when no entities exist', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin, entities: [] });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await expect(page.getByText(/no hay modelo de datos/i)).toBeVisible();
    await expect(page.getByText(/sube un JSON/i)).toBeVisible();
  });

  test('copy template button changes label to Copiado after click', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    // Grant clipboard write permission and mock clipboard API
    await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await page.getByRole('button', { name: /copiar plantilla/i }).click();

    await expect(page.getByRole('button', { name: /copiado/i })).toBeVisible();
  });

  test('download template button triggers template API call', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    const templateRequest = page.waitForRequest(
      (req) => req.url().includes('data-model-entities/template/') && req.method() === 'GET',
    );
    await page.getByRole('button', { name: /descargar plantilla/i }).click();
    await templateRequest;
    // Download was triggered (no error thrown — page still functional)
    await expect(page.getByRole('heading', { name: 'Modelo de datos', exact: true })).toBeVisible();
  });

  test('shows error message when upload returns server error', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath === 'accounts/projects/1/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
      }
      if (apiPath === 'accounts/projects/1/data-model-entities/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === 'accounts/projects/1/data-model-entities/' && method === 'POST') {
        return { status: 400, contentType: 'application/json', body: JSON.stringify({ detail: 'Invalid entities data.' }) };
      }
      if (apiPath === 'accounts/projects/1/data-model-entities/template/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockTemplate) };
      }
      if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
      }
      return null;
    });
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    const validJson = JSON.stringify({ entities: [{ name: 'Producto', description: '', keyFields: 'id', relationship: '' }] });
    await page.getByPlaceholder(/entities/i).fill(validJson);
    await page.getByRole('button', { name: /subir modelo de datos/i }).click();

    // Error message from the server is surfaced in the UI
    await expect(page.locator('text=/error|inválido|falló|no se pudo/i').first()).toBeVisible({ timeout: 10_000 });
  });
});

// ─── Client role ───────────────────────────────────────────────────────────────

test.describe('Platform Data Model — Client', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('upload card is not rendered for client role', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await expect(page.getByRole('button', { name: /subir modelo de datos/i })).not.toBeVisible();
    await expect(page.getByRole('button', { name: /copiar plantilla/i })).not.toBeVisible();
  });

  test('client sees entity table when entities exist', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await expect(page.getByRole('cell', { name: 'User', exact: true })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'Order' })).toBeVisible();
  });

  test('client sees empty state without admin hint when no entities exist', {
    tag: [...PLATFORM_PROJECT_DATA_MODEL, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient, entities: [] });
    await page.goto('/platform/projects/1/data-model', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Modelo de datos', exact: true }).waitFor({ state: 'visible', timeout: 30_000 });

    await expect(page.getByText(/no hay modelo de datos/i)).toBeVisible();
    await expect(page.getByText(/sube un JSON/i)).not.toBeVisible();
  });
});
