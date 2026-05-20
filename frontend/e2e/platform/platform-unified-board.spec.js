/**
 * E2E tests for the /platform/board route.
 *
 * @flow:platform-unified-board
 * The standalone unified board was removed in the platform IA refactor:
 * /platform/board now redirects authenticated users to /platform/projects
 * and unauthenticated users to the login page.
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

function setupBoardRedirectMocks(page, user) {
  return mockApi(page, async ({ apiPath, method }) => {
    if (apiPath === 'accounts/me/' && method === 'GET') return meResponse(user);
    if (apiPath === 'accounts/projects/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProjects) };
    }
    if (apiPath.startsWith('accounts/clients/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

test.describe('Platform Board Route', () => {
  // SPA routes need longer timeout for Vite on-demand compilation on dev server
  test.setTimeout(60_000);

  test('admin visiting /platform/board is redirected to projects', {
    tag: [...PLATFORM_UNIFIED_BOARD, '@role:platform-admin'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformAdmin });
    await setupBoardRedirectMocks(page, mockPlatformAdmin);
    await page.goto('/platform/board', { waitUntil: 'domcontentloaded' });

    await page.waitForURL('**/platform/projects**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/projects/);
  });

  test('client visiting /platform/board is redirected to projects', {
    tag: [...PLATFORM_UNIFIED_BOARD, '@role:platform-client'],
  }, async ({ page }) => {
    await setPlatformAuth(page, { user: mockPlatformClient });
    await setupBoardRedirectMocks(page, mockPlatformClient);
    await page.goto('/platform/board', { waitUntil: 'domcontentloaded' });

    await page.waitForURL('**/platform/projects**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/projects/);
  });

  test('unauthenticated user is redirected to login', {
    tag: [...PLATFORM_UNIFIED_BOARD, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/platform/board', { waitUntil: 'domcontentloaded' });
    await page.waitForURL('**/platform/login**', { timeout: 30000 });
    await expect(page).toHaveURL(/\/platform\/login/);
  });
});
