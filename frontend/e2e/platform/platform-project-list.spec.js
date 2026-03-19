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
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(projects) };
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
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Proyectos' })).toBeVisible();
    await expect(page.getByText('E-commerce Platform')).toBeVisible();
    await expect(page.getByText('Mobile App MVP')).toBeVisible();
    await expect(page.getByText('65%')).toBeVisible();
    await expect(page.getByText('Activo', { exact: true })).toBeVisible();
    await expect(page.getByText('Pausado', { exact: true })).toBeVisible();
  });

  test('shows status filter tabs for admin', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('button', { name: /todos/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /activos/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /pausados/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /completados/i })).toBeVisible();
  });

  test('shows Nuevo proyecto button for admin', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('button', { name: /nuevo proyecto/i })).toBeVisible();
  });

  test('shows empty state when no projects exist', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin, projects: [] });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText(/no hay proyectos creados/i)).toBeVisible();
  });

  test('clicking a project card navigates to project detail', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupProjectMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    const projectLink = page.getByRole('link', { name: /e-commerce platform/i });
    // i18n prefix strategy adds locale prefix to all hrefs
    await expect(projectLink).toHaveAttribute('href', /\/platform\/projects\/1$/);
  });
});

test.describe('Platform Project List — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client sees project list without create button and filters', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupProjectMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible();
    await expect(page.getByRole('button', { name: /nuevo proyecto/i })).not.toBeVisible();
    await expect(page.getByRole('button', { name: /todos/i })).not.toBeVisible();
  });

  test('client sees empty state message when no projects assigned', {
    tag: [...PLATFORM_PROJECT_LIST, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupProjectMocks(page, { user: mockPlatformClient, projects: [] });
    await page.goto('/platform/projects', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Mis proyectos' })).toBeVisible();
    await expect(page.getByText(/no tienes proyectos asignados/i)).toBeVisible();
  });
});
