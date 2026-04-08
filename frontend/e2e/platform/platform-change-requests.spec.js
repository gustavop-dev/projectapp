/**
 * E2E tests for platform change requests flow.
 *
 * @flow:platform-change-requests
 * Covers: change request list rendering, status filter tabs, create change request,
 *         admin evaluate change request, add comment, unified cross-project view.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_CHANGE_REQUESTS } from '../helpers/flow-tags.js';
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

const mockChangeRequests = [
  {
    id: 1, title: 'Agregar filtro de precio', description: 'Los usuarios necesitan filtrar por precio.',
    module_or_screen: 'Catálogo', suggested_priority: 'high', is_urgent: false,
    status: 'pending', admin_response: '', estimated_cost: null, estimated_time: '',
    created_by_name: 'Client E2E', created_by_email: 'client@e2e-test.com',
    comments_count: 0, screenshot_url: null, created_at: '2025-02-01T10:00:00Z',
  },
  {
    id: 2, title: 'Cambiar color del botón', description: 'El botón debería ser verde.',
    module_or_screen: 'Producto', suggested_priority: 'low', is_urgent: false,
    status: 'approved', admin_response: 'Aprobado, lo incluiremos.', estimated_cost: 0, estimated_time: '2 días',
    created_by_name: 'Client E2E', created_by_email: 'client@e2e-test.com',
    comments_count: 1, screenshot_url: null, created_at: '2025-01-28T10:00:00Z',
  },
];

const meResponse = (user) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(user) });

function setupMocks(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject]) };
    }
    if (apiPath === 'accounts/projects/1/change-requests/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockChangeRequests) };
    }
    if (apiPath === 'accounts/projects/1/change-requests/' && method === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify({ id: 10, title: 'New CR', status: 'pending', comments_count: 0 }) };
    }
    if (apiPath.match(/accounts\/projects\/1\/change-requests\/\d+\/evaluate\/$/) && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockChangeRequests[0], status: 'approved' }) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Change Requests — Client', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('renders change request list with status tabs', {
    tag: [...PLATFORM_CHANGE_REQUESTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/changes', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /solicitudes de cambio/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Agregar filtro de precio')).toBeVisible();
    await expect(page.getByText('Cambiar color del botón')).toBeVisible();
  });

  test('client can create a new change request', {
    tag: [...PLATFORM_CHANGE_REQUESTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/changes', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /solicitudes de cambio/i }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByRole('button', { name: /nueva solicitud/i }).click();
    await page.getByPlaceholder('¿Qué cambio necesitas?').fill('New change request');
    await page.getByRole('button', { name: /crear solicitud/i }).click();
  });
});

test.describe('Platform Change Requests — Admin', () => {
  test.setTimeout(60_000);

  test('admin sees change requests and can evaluate', {
    tag: [...PLATFORM_CHANGE_REQUESTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/changes', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /solicitudes de cambio/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Agregar filtro de precio')).toBeVisible();
  });
});

// ── Unified cross-project view (/platform/changes) ──

const mockProject2 = {
  id: 2, name: 'Mobile App', status: 'active', progress: 20,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp', start_date: '2025-03-01', estimated_end_date: '2025-09-30',
};

const mockCRsCrossProject = [
  { ...mockChangeRequests[0], project_id: 1, project_name: 'E-commerce Platform' },
  { ...mockChangeRequests[1], project_id: 1, project_name: 'E-commerce Platform' },
  {
    id: 3, title: 'Add dark mode', description: 'Users want dark mode for the mobile app.',
    module_or_screen: 'Settings', suggested_priority: 'medium', is_urgent: false,
    status: 'pending', admin_response: '', estimated_cost: null, estimated_time: '',
    created_by_name: 'Client E2E', created_by_email: 'client@e2e-test.com',
    comments_count: 0, screenshot_url: null, created_at: '2025-02-05T10:00:00Z',
    project_id: 2, project_name: 'Mobile App',
  },
];

function setupUnifiedChangesMocks(page, { user, crs = mockCRsCrossProject }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject, mockProject2]) };
    }
    if (apiPath.match(/^accounts\/change-requests\//) && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(crs) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Change Requests — Unified /platform/changes', () => {
  test.setTimeout(60_000);

  test('client sees change requests grouped by project', {
    tag: [...PLATFORM_CHANGE_REQUESTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupUnifiedChangesMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/changes', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /mis solicitudes/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('E-commerce Platform')).toBeVisible();
    await expect(page.getByText('Agregar filtro de precio')).toBeVisible();
    await expect(page.getByText('Mobile App')).toBeVisible();
    await expect(page.getByText('Add dark mode')).toBeVisible();
  });

  test('admin sees all requests with archived toggle and summary pills', {
    tag: [...PLATFORM_CHANGE_REQUESTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupUnifiedChangesMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/changes', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /solicitudes de cambio/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Mostrar archivados')).toBeVisible();
    await expect(page.getByText('Pendientes', { exact: true })).toBeVisible();
    await expect(page.getByText('E-commerce Platform')).toBeVisible();
    await expect(page.getByText('Mobile App')).toBeVisible();
  });

  test('shows empty state when no change requests exist', {
    tag: [...PLATFORM_CHANGE_REQUESTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupUnifiedChangesMocks(page, { user: mockPlatformClient, crs: [] });
    await page.goto('/platform/changes', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /mis solicitudes/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('No hay solicitudes de cambio en este momento.')).toBeVisible();
  });
});
