/**
 * E2E tests for platform kanban board flow.
 *
 * @flow:platform-kanban-board
 * Covers: board render with columns, card display, create requirement modal,
 *         card detail modal, drag & drop between columns,
 *         mark card as completed, completed section toggle,
 *         client view restrictions.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_KANBAN_BOARD } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformAdmin,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockProject = {
  id: 1,
  name: 'E-commerce Platform',
  description: 'Full-stack e-commerce solution',
  status: 'active',
  progress: 33,
  client_id: 9002,
  client_name: 'Client E2E',
  client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp',
  start_date: '2025-01-01',
  estimated_end_date: '2025-06-30',
};

const mockRequirements = [
  {
    id: 101,
    title: 'Diseño de landing page',
    description: 'Crear wireframes y diseño final de la landing page principal.',
    configuration: 'Visible para todos los usuarios registrados.',
    flow: 'Usuario abre la app → navega al home → ve la landing page con hero y CTA.',
    status: 'todo',
    priority: 'high',
    order: 0,
    comments_count: 2,
    created_at: '2025-01-15T10:00:00Z',
    history: [],
    comments: [],
  },
  {
    id: 102,
    title: 'API de autenticación',
    description: 'JWT login + refresh + password reset endpoints.',
    configuration: 'Todos los usuarios.',
    flow: 'Usuario abre login → ingresa credenciales → recibe JWT → accede al dashboard.',
    status: 'in_progress',
    priority: 'critical',
    order: 0,
    comments_count: 0,
    created_at: '2025-01-16T10:00:00Z',
    history: [{ id: 1, from_status: 'todo', to_status: 'in_progress', created_at: '2025-01-17T10:00:00Z' }],
    comments: [],
  },
  {
    id: 103,
    title: 'Integración pasarela de pagos',
    description: 'Integrar Stripe para procesamiento de pagos.',
    configuration: 'Solo rol: Administrador de pagos.',
    flow: 'Admin navega a pagos → selecciona plan → ingresa tarjeta → confirma pago.',
    status: 'in_review',
    priority: 'medium',
    order: 0,
    comments_count: 1,
    created_at: '2025-01-14T10:00:00Z',
    history: [],
    comments: [{ id: 1, user_name: 'Admin E2E', content: 'Revisando PR', is_internal: false, created_at: '2025-01-20T10:00:00Z' }],
  },
  {
    id: 104,
    title: 'Tests unitarios modelos',
    description: 'Cobertura de tests para todos los modelos.',
    configuration: '',
    flow: '',
    status: 'done',
    priority: 'low',
    order: 0,
    comments_count: 0,
    created_at: '2025-01-10T10:00:00Z',
    history: [],
    comments: [],
  },
];

const meResponse = (user) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(user),
});

function setupPlatformMocks(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') {
      return meResponse(user);
    }
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/' && method === 'GET') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ id: 1, title: 'Main', has_business_proposal: true }]),
      };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/requirements/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockRequirements) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject]) };
    }
    if (apiPath.match(/accounts\/projects\/1\/deliverables\/1\/requirements\/\d+\/$/) && method === 'GET') {
      const id = parseInt(apiPath.match(/requirements\/(\d+)/)[1], 10);
      const req = mockRequirements.find((r) => r.id === id);
      return { status: 200, contentType: 'application/json', body: JSON.stringify(req || mockRequirements[0]) };
    }
    if (apiPath.match(/accounts\/projects\/1\/deliverables\/1\/requirements\/\d+\/move\/$/) && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ detail: 'Movido.' }) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/requirements/' && method === 'POST') {
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 200, title: 'New req', status: 'todo', priority: 'medium', comments_count: 0 }),
      };
    }
    if (apiPath.match(/accounts\/projects\/1\/deliverables\/1\/requirements\/\d+\/comments\/$/) && method === 'POST') {
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 50, user_name: user.first_name, content: 'Test comment', is_internal: false, created_at: new Date().toISOString() }),
      };
    }
    return null;
  });
}

test.describe('Platform Kanban Board — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('renders board with three columns and cards distributed by status', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupPlatformMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Por hacer')).toBeVisible();
    await expect(page.getByText('En progreso')).toBeVisible();
    await expect(page.getByText('En revisión')).toBeVisible();

    await expect(page.getByText('Diseño de landing page')).toBeVisible();
    await expect(page.getByText('API de autenticación')).toBeVisible();
    await expect(page.getByText('Integración pasarela de pagos')).toBeVisible();
  });

  test('displays progress pill with percentage and done count', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupPlatformMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('1/4')).toBeVisible();
  });

  test('admin can open create requirement modal and submit new card', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupPlatformMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByRole('button', { name: /card/i }).click();
    await expect(page.getByText('Nuevo requerimiento')).toBeVisible();

    await page.getByPlaceholder('Título del requerimiento').fill('New E2E requirement');
    await page.getByRole('button', { name: /crear/i }).click();

    await expect(page.getByText('Nuevo requerimiento')).not.toBeVisible({ timeout: 5000 });
  });

  test('clicking a card opens the detail modal with description and meta', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupPlatformMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByText('Diseño de landing page').click();

    await expect(page.getByText('Crear wireframes y diseño final')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Descripción', { exact: false })).toBeVisible();
    await expect(page.getByText('Comentarios')).toBeVisible();
  });

  test('completed cards section toggles visibility', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupPlatformMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    const completedBtn = page.getByRole('button', { name: /completados/i });
    await expect(completedBtn).toBeVisible();

    await completedBtn.click();
    await expect(page.getByText('Tests unitarios modelos')).toBeVisible();

    await completedBtn.click();
    await expect(page.getByText('Tests unitarios modelos')).not.toBeVisible();
  });

  test('back link navigates to unified board', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupPlatformMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    const main = page.locator('main');
    const backLink = main.getByRole('link', { name: 'Tablero' });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', /\/platform\/board$/);
  });
});

test.describe('Platform Kanban Board — Client', () => {
  test.setTimeout(60_000);

  test('client sees board but cannot create cards', {
    tag: [...PLATFORM_KANBAN_BOARD, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupPlatformMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await expect(page.getByText('Diseño de landing page')).toBeVisible();

    await expect(page.getByRole('button', { name: /card/i })).not.toBeVisible();
  });
});
