/**
 * E2E tests for platform admin quick-access flow.
 *
 * @flow:platform-access-view
 * Covers: project card grid, URL rows, credential copy/reveal,
 *         search filtering, empty states, admin-only access guard.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_ACCESS_VIEW } from '../helpers/flow-tags.js';
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
    id: 101,
    name: 'Mi Huella Digital',
    status: 'active',
    client_name: 'Carlos Gómez',
    client_company: 'ACME Corp',
    client_email: 'carlos@acme.com',
    production_url: 'https://mihuella.co',
    staging_url: 'https://staging.mihuella.co',
    admin_url: 'https://mihuella.co/admin/',
    repository_url: 'https://github.com/acme/mihuella',
    admin_username: 'superadmin',
    admin_password: 's3cr3t!',
  },
  {
    id: 102,
    name: 'Sin URLs',
    status: 'paused',
    client_name: 'Ana Pérez',
    client_company: '',
    client_email: 'ana@email.com',
    production_url: '',
    staging_url: '',
    admin_url: '',
    repository_url: '',
    admin_username: '',
    admin_password: '',
  },
];

function setupAccessMocks(page, projects = mockProjects) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformAdmin);
    if (apiPath === 'accounts/projects/access/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(projects) };
    }
    return null;
  });
}

test.describe('Platform Access View', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders page heading', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('heading', { name: 'Accesos' })).toBeVisible();
  });

  test('renders project cards with name and client', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Mi Huella Digital')).toBeVisible();
    await expect(page.getByText('ACME Corp')).toBeVisible();
  });

  test('renders status badge for each project', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Activo', { exact: true })).toBeVisible();
    await expect(page.getByText('Pausado', { exact: true })).toBeVisible();
  });

  test('renders URL rows for project with configured URLs', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    const card = page.locator('[data-testid="access-card"]').first();
    // Each URL row has a label + link with the same substring; scope to the label span
    // rather than the link.
    await expect(card.getByText('Producción', { exact: true })).toBeVisible();
    await expect(card.getByText('Staging', { exact: true })).toBeVisible();
    await expect(card.getByText('Admin Django', { exact: true })).toBeVisible();
    await expect(card.getByText('Repositorio', { exact: true })).toBeVisible();
  });

  test('shows credential copy fields when username and password are set', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    const card = page.locator('[data-testid="access-card"]').first();
    await expect(card.getByText('superadmin')).toBeVisible();
  });

  test('reveals password on toggle button click', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    const card = page.locator('[data-testid="access-card"]').first();
    const revealBtn = card.getByRole('button', { name: 'Revelar' });
    await revealBtn.click();
    await expect(card.getByRole('button', { name: 'Ocultar' })).toBeVisible();
  });

  test('shows no-credential message for project without credentials', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    const cards = page.locator('[data-testid="access-card"]');
    const secondCard = cards.nth(1);
    await expect(secondCard.getByText(/Sin credenciales/)).toBeVisible();
  });

  test('filters cards by search term', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await page.getByPlaceholder('Buscar por proyecto, cliente o URL').fill('huella');
    await expect(page.getByText('Mi Huella Digital')).toBeVisible();
    await expect(page.getByText('Sin URLs')).not.toBeVisible();
  });

  test('shows no-match message when search finds nothing', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await page.getByPlaceholder('Buscar por proyecto, cliente o URL').fill('zzznomatch');
    await expect(page.getByText('Ningún proyecto coincide con esa búsqueda.')).toBeVisible();
  });

  test('shows empty state when no projects are returned', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page, []);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await expect(page.getByText('Todavía no hay proyectos con accesos configurados.')).toBeVisible();
  });

  test('shows refresh button', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupAccessMocks(page);
    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });

    await expect(page.getByRole('button', { name: 'Actualizar' })).toBeVisible();
  });
});

test.describe('Platform Access View — Access Guard', () => {
  test.setTimeout(60_000);

  test('client role is redirected away from access page', {
    tag: [...PLATFORM_ACCESS_VIEW, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });

    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(mockPlatformClient);
      return null;
    });

    await page.goto('/platform/access', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/dashboard', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/dashboard/);
  });
});
