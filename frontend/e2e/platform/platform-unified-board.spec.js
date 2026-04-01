/**
 * E2E tests for platform unified board flow.
 *
 * @flow:platform-unified-board
 * Covers: unified board render at /platform/board,
 *         aggregated view of all project requirements,
 *         unauthenticated redirect.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PLATFORM_UNIFIED_BOARD } from '../helpers/flow-tags.js';
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
  { id: 1, name: 'Project Alpha', status: 'active', progress: 50 },
  { id: 2, name: 'Project Beta', status: 'active', progress: 30 },
];

const mockRequirements = [
  { id: 101, title: 'Task Alpha-1', status: 'todo', priority: 'high', module: 'Frontend', estimated_hours: 8, comments_count: 0 },
  { id: 201, title: 'Task Beta-1', status: 'in_progress', priority: 'medium', module: 'Backend', estimated_hours: 12, comments_count: 1 },
];

function setupUnifiedBoardMocks(page, user) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProjects) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 1, title: 'Main' }]) };
    }
    if (apiPath === 'accounts/projects/2/deliverables/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([{ id: 2, title: 'Main' }]) };
    }
    if (apiPath === 'accounts/projects/1/deliverables/1/requirements/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockRequirements[0]]) };
    }
    if (apiPath === 'accounts/projects/2/deliverables/2/requirements/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([mockRequirements[1]]) };
    }
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

test.describe('Platform Unified Board', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('admin can access unified board at /platform/board', {
    tag: [...PLATFORM_UNIFIED_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupUnifiedBoardMocks(page, mockPlatformAdmin);
    await page.goto('/platform/board', { waitUntil: 'domcontentloaded' });

    // Admin sees 'Actividad general' heading in the unified board
    await expect(page.locator('main').getByRole('heading', { name: /actividad general/i })).toBeVisible();
  });

  test('client can access unified board at /platform/board', {
    tag: [...PLATFORM_UNIFIED_BOARD, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupUnifiedBoardMocks(page, mockPlatformClient);
    await page.goto('/platform/board', { waitUntil: 'domcontentloaded' });

    // Client sees 'Mi tablero' heading
    await expect(page.locator('main').getByRole('heading', { name: /tablero/i })).toBeVisible();
  });

  test('unauthenticated user is redirected to login', {
    tag: [...PLATFORM_UNIFIED_BOARD, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/platform/board', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/login**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/login/);
  });
});
