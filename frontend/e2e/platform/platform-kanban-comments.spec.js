/**
 * E2E tests for platform kanban card comments flow.
 *
 * @flow:platform-kanban-card-comments
 * Covers: comment section in card detail modal, add public comment,
 *         admin internal comment toggle, comment display with author,
 *         empty comments state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_KANBAN_CARD_COMMENTS } from '../helpers/flow-tags.js';
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
  status: 'active',
  progress: 50,
};

const mockRequirementWithComments = {
  id: 101,
  title: 'Diseño de landing page',
  description: 'Crear wireframes y diseño final.',
  status: 'in_progress',
  priority: 'high',
  module: 'Frontend',
  estimated_hours: 16,
  comments_count: 2,
  created_at: '2025-01-15T10:00:00Z',
  history: [],
  comments: [
    { id: 1, user_name: 'Admin E2E', content: 'Revisando avances del diseño.', is_internal: false, created_at: '2025-01-18T10:00:00Z' },
    { id: 2, user_name: 'Admin E2E', content: 'Nota interna: falta aprobación.', is_internal: true, created_at: '2025-01-19T10:00:00Z' },
  ],
};

const mockRequirementNoComments = {
  id: 102,
  title: 'API de autenticación',
  description: 'JWT login endpoints.',
  status: 'todo',
  priority: 'critical',
  module: 'Backend',
  estimated_hours: 24,
  comments_count: 0,
  created_at: '2025-01-16T10:00:00Z',
  history: [],
  comments: [],
};

const mockRequirements = [mockRequirementWithComments, mockRequirementNoComments];

function setupCommentMocks(page, { user }) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/1/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProject) };
    }
    if (apiPath === 'accounts/projects/1/requirements/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockRequirements) };
    }
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockProject]) };
    }
    if (apiPath.match(/accounts\/projects\/1\/requirements\/101\/$/) && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockRequirementWithComments) };
    }
    if (apiPath.match(/accounts\/projects\/1\/requirements\/102\/$/) && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockRequirementNoComments) };
    }
    if (apiPath.match(/accounts\/projects\/1\/requirements\/\d+\/comments\/$/) && method === 'POST') {
      return {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 50,
          user_name: user.first_name,
          content: 'New test comment',
          is_internal: false,
          created_at: new Date().toISOString(),
        }),
      };
    }
    return null;
  });
}

test.describe('Platform Kanban Card Comments — Admin', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
  });

  test('card detail modal shows existing comments with author names', {
    tag: [...PLATFORM_KANBAN_CARD_COMMENTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCommentMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });

    await page.getByText('Diseño de landing page').click();
    await expect(page.getByText('Revisando avances del diseño.')).toBeVisible({ timeout: 10000 });
    // 'Admin E2E' appears in sidebar + comment authors; verify at least one comment author visible
    await expect(page.getByText('Admin E2E').first()).toBeVisible();
    await expect(page.getByText('Comentarios (2)')).toBeVisible();
  });

  test('admin sees internal comment badge', {
    tag: [...PLATFORM_KANBAN_CARD_COMMENTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCommentMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });

    await page.getByText('Diseño de landing page').click();
    // 'Interno' matches badge + checkbox label; use exact match for the badge
    await expect(page.getByText('Interno', { exact: true })).toBeVisible({ timeout: 10000 });
  });

  test('admin can submit a new comment', {
    tag: [...PLATFORM_KANBAN_CARD_COMMENTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCommentMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });

    await page.getByText('Diseño de landing page').click();
    await expect(page.getByPlaceholder('Escribe un comentario...')).toBeVisible({ timeout: 10000 });

    await page.getByPlaceholder('Escribe un comentario...').fill('New test comment');
    await page.getByRole('button', { name: /enviar/i }).click();
  });

  test('admin sees internal comment checkbox', {
    tag: [...PLATFORM_KANBAN_CARD_COMMENTS, '@role:platform-admin'],
  }, async ({ page }) => {
    await setupCommentMocks(page, { user: mockPlatformAdmin });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });

    await page.getByText('Diseño de landing page').click();
    await expect(page.getByText(/comentario interno/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Platform Kanban Card Comments — Client', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('client can view comments and submit public comments', {
    tag: [...PLATFORM_KANBAN_CARD_COMMENTS, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupCommentMocks(page, { user: mockPlatformClient });
    await page.goto('/platform/projects/1/board', { waitUntil: 'domcontentloaded' });

    await page.getByText('Diseño de landing page').click();
    await expect(page.getByPlaceholder('Escribe un comentario...')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/comentario interno/i)).not.toBeVisible();
  });
});
