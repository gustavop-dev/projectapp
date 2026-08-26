/**
 * E2E tests for platform project list flow.
 *
 * @flow:platform-project-list
 * Covers: project list render, project cards with progress bar,
 *         status filter tabs (admin), empty state,
 *         navigation to project detail, create project button (admin),
 *         client view without create button.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_PROJECT_LIST } from '../helpers/flow-tags.js';
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

const mockProjects = [
  {
    id: 1,
    name: 'E-commerce Platform',
    description: 'Full-stack e-commerce solution',
    status: 'active',
    status_label: 'Activo',
    current_state: {
      id: 2,
      name: 'Activo',
      system_key: 'active',
      operational_effect: 'operating',
      color: 'emerald',
    },
    progress: 65,
    client_id: 9002,
    client_name: 'Client E2E',
    client_email: 'client@e2e-test.com',
    client_company: 'ACME Corp',
    start_date: '2025-01-01',
    estimated_end_date: '2025-06-30',
  },
  {
    id: 2,
    name: 'Mobile App MVP',
    description: 'React Native mobile application',
    status: 'paused',
    status_label: 'Pausado',
    current_state: {
      id: 3,
      name: 'Pausado',
      system_key: 'paused',
      operational_effect: 'paused',
      color: 'yellow',
    },
    progress: 20,
    client_id: 9002,
    client_name: 'Client E2E',
    client_email: 'client@e2e-test.com',
    client_company: 'ACME Corp',
    start_date: '2025-02-01',
    estimated_end_date: '2025-08-30',
  },
];

const mockClients = [
  {
    user_id: 9002,
    first_name: 'Client',
    last_name: 'E2E',
    email: 'client@e2e-test.com',
    company_name: 'ACME Corp',
    is_active: true,
    is_onboarded: true,
  },
];

function setupProjectMocks(page, { user, projects = mockProjects }) {
  return mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      // The status-filter tabs re-fetch with ?status=<value>; honor it so
      // tests can assert the list actually narrows, not just that it re-requests.
      const status = new URL(route.request().url()).searchParams.get('status');
      const filtered = status ? projects.filter((p) => p.status === status) : projects;
      return { status: 200, contentType: 'application/json', body: JSON.stringify(filtered) };
    }
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockClients) };
    }
    return null;
  });
}

test.describe('Platform Project List — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders project list with cards showing name, status, and progress', {
    tag: ['@outcome:display', ...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (content-bearing data assertions against the fixture — name, progress and status values)
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Proyectos' })).toBeVisible();
    await expect(page.getByText('E-commerce Platform')).toBeVisible();
    await expect(page.getByText('Mobile App MVP')).toBeVisible();
    await expect(page.getByText('65%')).toBeVisible();
    await expect(
      page.getByTestId('project-row-1').getByText('Activo', { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByTestId('project-row-2').getByText('Pausado', { exact: true }),
    ).toBeVisible();
    // Merged from the deleted 'shows Nuevo proyecto button for admin' test
    // (same route/mocks, redundant standalone test).
    await expect(page.getByRole('button', { name: /nuevo proyecto/i })).toBeVisible();
  });

  test('filters projects with state controls derived from the returned catalog', {
    tag: ['@outcome:success', ...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('button', { name: 'Todos', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Activo', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Pausado', exact: true })).toBeVisible();

    await expect(page.getByText('E-commerce Platform')).toBeVisible();
    await expect(page.getByText('Mobile App MVP')).toBeVisible();

    // Selecting the catalog state narrows the already-fetched project rows.
    await page.getByRole('button', { name: 'Activo', exact: true }).click();

    await expect(page.getByText('Mobile App MVP')).not.toBeVisible();
    await expect(page.getByText('E-commerce Platform')).toBeVisible();
  });

  test('shows empty state when no projects exist', {
    tag: ['@outcome:display', ...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (content-bearing empty state; negative counterpart anchored by the positive-content test above)
    await setupProjectMocks(page, { user: mockPlatformAdmin, projects: [] });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/no hay proyectos creados/i)).toBeVisible();
  });

  test('clicking a project row navigates to project detail', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    const projectRow = page.getByTestId('project-row-1');
    await expect(projectRow).toBeVisible();
    await projectRow.click();

    // i18n prefix strategy adds locale prefix to all routes
    await expect(page).toHaveURL(/\/platform\/projects\/1$/);
  });
});

test.describe('Platform Project List — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client sees project list without create button and filters', {
    tag: ['@outcome:display', ...PLATFORM_PROJECT_LIST, '@role:platform-client'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (content-bearing negative assertions, anchored by the positive heading check first)
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupProjectMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible();
    await expect(page.getByRole('button', { name: /nuevo proyecto/i })).not.toBeVisible();
    await expect(page.getByRole('button', { name: /todos/i })).not.toBeVisible();
  });

  test('client sees empty state message when no projects assigned', {
    tag: ['@outcome:display', ...PLATFORM_PROJECT_LIST, '@role:platform-client'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (content-bearing empty state, anchored by the positive heading check first)
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupProjectMocks(page, { user: mockPlatformClient, projects: [] });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible();
    await expect(page.getByText(/no tienes proyectos asignados/i)).toBeVisible();
  });
});
