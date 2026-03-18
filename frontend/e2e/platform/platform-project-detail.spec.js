/**
 * E2E tests for platform project detail flow.
 *
 * @flow:platform-project-detail
 * Covers: project detail render with stats, module cards,
 *         back link to projects, edit modal (admin),
 *         not found state, board link navigation.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_PROJECT_DETAIL } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

const mockProject = {
  id: 1,
  name: 'E-commerce Platform',
  description: 'Full-stack e-commerce solution',
  status: 'active',
  progress: 65,
  client_id: 9002,
  client_name: 'Client E2E',
  client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp',
  start_date: '2025-01-01',
  estimated_end_date: '2025-06-30',
};

function setupDetailMocks(page, { user, project = mockProject }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(project) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([project]) };
    }
    if (apiPath === 'accounts/projects/1/' && method === 'PATCH') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...project, name: 'Updated Name' }) };
    }
    return null;
  });
}

test.describe('Platform Project Detail — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders project detail with name, status badge, and stats', {
    tag: [...PLATFORM_PROJECT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupDetailMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1', { waitUntil: 'domcontentloaded' });

    const main = page.locator('main');
    await expect(main.getByText('E-commerce Platform')).toBeVisible();
    await expect(main.getByText('Activo', { exact: true })).toBeVisible();
    await expect(main.getByText('65%')).toBeVisible();
    await expect(main.getByText('ACME Corp')).toBeVisible();
    await expect(main.getByText('Progreso')).toBeVisible();
    await expect(main.getByText('Cliente', { exact: true })).toBeVisible();
  });

  test('shows back link to projects list', {
    tag: [...PLATFORM_PROJECT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupDetailMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1', { waitUntil: 'domcontentloaded' });

    const backLink = page.locator('main').getByRole('link', { name: /proyectos/i });
    await expect(backLink).toBeVisible();
    // i18n prefix strategy adds locale prefix to all hrefs
    await expect(backLink).toHaveAttribute('href', /\/platform\/projects$/);
  });

  test('renders module cards including Tablero with link to board', {
    tag: [...PLATFORM_PROJECT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupDetailMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1', { waitUntil: 'domcontentloaded' });

    await expect(page.locator('main').getByRole('heading', { name: 'Tablero' })).toBeVisible();
    const boardLink = page.locator('main').getByRole('link', { name: /tablero/i });
    // i18n prefix strategy adds locale prefix to all hrefs
    await expect(boardLink).toHaveAttribute('href', /\/platform\/projects\/1\/board$/);
  });

  test('admin sees Editar button', {
    tag: [...PLATFORM_PROJECT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupDetailMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('button', { name: /editar/i })).toBeVisible();
  });

  test('shows not found state for invalid project ID', {
    tag: [...PLATFORM_PROJECT_DETAIL, '@role:platform-admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
      if (apiPath === 'accounts/projects/999/' && method === 'GET') {
        return { status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'No encontrado' }) };
      }
      return null;
    });
    await page.goto('/platform/projects/999', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/proyecto no encontrado/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /volver a proyectos/i })).toBeVisible();
  });
});

test.describe('Platform Project Detail — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client sees project detail without edit button', {
    tag: [...PLATFORM_PROJECT_DETAIL, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupDetailMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('E-commerce Platform')).toBeVisible();
    await expect(page.getByRole('button', { name: /editar/i })).not.toBeVisible();
  });
});
