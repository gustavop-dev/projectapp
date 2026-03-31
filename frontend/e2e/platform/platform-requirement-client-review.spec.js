/**
 * E2E tests for platform requirement client review flow.
 *
 * @flow:platform-requirement-client-review
 * Covers: client clicks completed requirement, sees approve/change/bug options,
 *         approve action, navigate to change requests, navigate to bug reports.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_REQUIREMENT_CLIENT_REVIEW } from '../helpers/flow-tags.js';
import {
  setPlatformAuth,
  mockPlatformClient,
} from '../helpers/platform-auth.js';

const mockProject = {
  id: 1, name: 'E-commerce Platform', status: 'active', progress: 50,
  client_id: 9002, client_name: 'Client E2E', client_email: 'client@e2e-test.com',
  client_company: 'ACME Corp', start_date: '2025-01-01', estimated_end_date: '2025-06-30',
};

const mockRequirements = [
  {
    id: 101, title: 'Login de usuario', description: 'Pantalla de autenticación.',
    configuration: 'Todos los usuarios.', flow: 'Abre app → login → dashboard.',
    status: 'done', priority: 'high', order: 0, comments_count: 0,
    created_at: '2025-01-15T10:00:00Z',
    history: [{ id: 1, from_status: 'in_review', to_status: 'done', changed_by_email: 'admin@test.com', created_at: '2025-02-01T10:00:00Z' }],
    comments: [],
  },
  {
    id: 102, title: 'Catálogo de productos', description: 'Listado con filtros.',
    configuration: 'Usuarios registrados.', flow: 'Navega al catálogo → filtra → click producto.',
    status: 'todo', priority: 'medium', order: 0, comments_count: 0,
    created_at: '2025-01-16T10:00:00Z', history: [], comments: [],
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
    if (apiPath.match(/accounts\/projects\/1\/deliverables\/1\/requirements\/\d+\/$/) && method === 'GET') {
      const id = parseInt(apiPath.match(/requirements\/(\d+)/)[1], 10);
      const req = mockRequirements.find((r) => r.id === id);
      return { status: 200, contentType: 'application/json', body: JSON.stringify(req || mockRequirements[0]) };
    }
    if (apiPath.match(/accounts\/projects\/1\/deliverables\/1\/requirements\/\d+\/move\/$/) && method === 'POST') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...mockRequirements[0], status: 'done' }) };
    }
    if (apiPath === 'accounts/notifications/unread-count/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ unread_count: 0 }) };
    }
    return null;
  });
}

test.describe('Platform Requirement Client Review', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
  });

  test('client sees completed requirements in the Completados section', {
    tag: [...PLATFORM_REQUIREMENT_CLIENT_REVIEW, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    const completedBtn = page.getByRole('button', { name: /completados/i });
    await expect(completedBtn).toBeVisible();
    await completedBtn.click();

    await expect(page.getByText('Login de usuario')).toBeVisible();
  });

  test('clicking a completed card shows review actions (approve, change, bug)', {
    tag: [...PLATFORM_REQUIREMENT_CLIENT_REVIEW, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByRole('button', { name: /completados/i }).click();
    await page.getByText('Login de usuario').click();

    await expect(page.getByText(/cumple con lo esperado/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /aprobar/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /solicitar cambio/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /reportar bug/i })).toBeVisible();
  });

  test('solicitar cambio link navigates to change requests with pre-filled data', {
    tag: [...PLATFORM_REQUIREMENT_CLIENT_REVIEW, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByRole('button', { name: /completados/i }).click();
    await page.getByText('Login de usuario').click();
    await page.getByText(/cumple con lo esperado/i).waitFor({ state: 'visible', timeout: 10000 });

    const changeLink = page.getByRole('link', { name: /solicitar cambio/i });
    await expect(changeLink).toHaveAttribute('href', /\/changes\?from_req=101/);
  });

  test('reportar bug link navigates to bugs with pre-filled data', {
    tag: [...PLATFORM_REQUIREMENT_CLIENT_REVIEW, '@role:platform-client'],
  }, async ({ page }) => {
    await setupMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });
    await page.getByRole('heading', { name: 'Tablero' }).waitFor({ state: 'visible', timeout: 30000 });

    await page.getByRole('button', { name: /completados/i }).click();
    await page.getByText('Login de usuario').click();
    await page.getByText(/cumple con lo esperado/i).waitFor({ state: 'visible', timeout: 10000 });

    const bugLink = page.getByRole('link', { name: /reportar bug/i });
    await expect(bugLink).toHaveAttribute('href', /\/bugs\?from_req=101/);
  });
});
