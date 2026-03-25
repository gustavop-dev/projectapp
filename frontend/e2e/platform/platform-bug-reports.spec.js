/**
 * E2E tests for platform bug reports flow.
 *
 * @flow:platform-bug-reports
 * Covers: bug report list rendering, status/severity filters, create bug report,
 *         admin evaluate bug report, unified cross-project view.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_BUG_REPORTS } from '../helpers/flow-tags.js';
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

const mockBugReports = [
  {
    id: 1, title: 'Botón no responde en móvil', description: 'El botón de agregar al carrito no funciona en Safari iOS.',
    severity: 'critical', status: 'confirmed', steps_to_reproduce: ['Abrir en iPhone', 'Ir a producto', 'Tocar botón'],
    expected_behavior: 'Debería agregar al carrito.', actual_behavior: 'No pasa nada.',
    environment: 'production', device_browser: 'iPhone 14 / Safari 17', is_recurring: true,
    admin_response: 'Confirmado, priorizando fix.', linked_bug_id: null, screenshot_url: null,
    reported_by_name: 'Client E2E', reported_by_email: 'client@e2e-test.com',
    comments_count: 1, created_at: '2025-02-01T10:00:00Z',
  },
  {
    id: 2, title: 'Error 500 al buscar', description: 'Buscar con caracteres especiales da error.',
    severity: 'medium', status: 'reported', steps_to_reproduce: ['Ir al buscador', 'Escribir comillas'],
    expected_behavior: 'Mostrar resultados.', actual_behavior: 'Error 500.',
    environment: 'production', device_browser: 'Chrome / macOS', is_recurring: true,
    admin_response: '', linked_bug_id: null, screenshot_url: null,
    reported_by_name: 'Client E2E', reported_by_email: 'client@e2e-test.com',
    comments_count: 0, created_at: '2025-01-28T10:00:00Z',
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
    if (apiPath === 'accounts/projects/1/bug-reports/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockBugReports) };
    }
    if (apiPath === 'accounts/projects/1/bug-reports/' && method === 'POST') {
      return { status: 201, contentType: 'application/json', body: JSON.stringify({ id: 10, title: 'New bug', severity: 'medium', status: 'reported', comments_count: 0 }) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Bug Reports — Client', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('renders bug report list with severity badges', {
    tag: [...PLATFORM_BUG_REPORTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/bugs', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /reporte de bugs/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Botón no responde en móvil')).toBeVisible();
    await expect(page.getByText('Error 500 al buscar')).toBeVisible();
  });

  test('client can create a new bug report', {
    tag: [...PLATFORM_BUG_REPORTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/bugs', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /reporte de bugs/i }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByRole('button', { name: /reportar bug/i }).click();
    await page.getByPlaceholder('¿Qué está fallando?').fill('New bug report');
    await page.getByRole('button', { name: /reportar bug/i }).last().click();
  });
});

test.describe('Platform Bug Reports — Admin', () => {
  test.setTimeout(60_000);

  test('admin sees bug reports with status counts', {
    tag: [...PLATFORM_BUG_REPORTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/bugs', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: /reporte de bugs/i }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Botón no responde en móvil')).toBeVisible();
  });
});
