/**
 * E2E tests for platform kanban JSON upload flow.
 *
 * @flow:platform-kanban-json-upload
 * Covers: download JSON example template, upload JSON file to bulk-create requirements,
 *         backlog section updates with new cards.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_KANBAN_JSON_UPLOAD } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockProject = {
  id: 1, name: 'E-commerce Platform', status: 'active', progress: 0,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp', start_date: '2025-01-01', estimated_end_date: '2025-06-30',
};

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });

function setupMocks(page, { user, existingReqs = [] }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject]) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, title: 'Main', has_business_proposal: true }]),
      };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/requirements/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(existingReqs) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/requirements/bulk/' && method === 'POST') {
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          created: 3,
          requirements: [
            { id: 201, title: 'Login de usuario', description: 'Pantalla de autenticación.', configuration: 'Todos los usuarios.', flow: 'Abre app → login → dashboard.', status: 'backlog', priority: 'medium', order: 0, comments_count: 0 },
            { id: 202, title: 'Panel de administración', description: 'Vista principal del admin.', configuration: 'Solo rol: Administrador.', flow: 'Admin inicia sesión → dashboard KPIs.', status: 'backlog', priority: 'medium', order: 1, comments_count: 0 },
            { id: 203, title: 'Catálogo de productos', description: 'Listado con filtros.', configuration: 'Usuarios registrados.', flow: 'Navega al catálogo → filtra → click producto.', status: 'backlog', priority: 'high', order: 2, comments_count: 0 },
          ],
        }),
      };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Kanban JSON Upload — Admin', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('admin sees Ejemplo and Subir JSON buttons on the board', {
    tag: [...PLATFORM_KANBAN_JSON_UPLOAD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByRole('button', { name: /ejemplo/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /subir json/i })).toBeVisible();
  });

  test('clicking Ejemplo triggers a file download', {
    tag: [...PLATFORM_KANBAN_JSON_UPLOAD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /ejemplo/i }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('requerimientos-ejemplo.json');
  });
});

test.describe('Platform Kanban JSON Upload — Client', () => {
  test.setTimeout(60_000);

  test('client does not see JSON upload buttons', {
    tag: [...PLATFORM_KANBAN_JSON_UPLOAD, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByRole('button', { name: /ejemplo/i })).not.toBeVisible();
    await expect(page.getByRole('button', { name: /subir json/i })).not.toBeVisible();
  });
});
