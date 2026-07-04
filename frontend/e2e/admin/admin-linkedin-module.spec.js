/**
 * E2E tests for the LinkedIn content module at /panel/linkedin.
 *
 * Covers flow: admin-linkedin-module
 *   - Disconnected state shows "Conectar LinkedIn" button.
 *   - Connected state shows profile name and token expiry date.
 *   - Posts list renders rows with status chips.
 *   - Create modal saves a draft and the list refreshes.
 *   - Publish now (with confirm) flips the row to published.
 *   - Publish API failure surfaces an inline error message.
 *
 * All API endpoints are mocked — no real LinkedIn calls.
 */

import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_LINKEDIN_MODULE } from '../helpers/flow-tags.js';

test.setTimeout(60_000);

// ─────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const disconnectedStatus = { connected: false };

const connectedStatus = {
  connected: true,
  profile_name: 'Gustavo Pérez',
  profile_email: 'gustavo@example.com',
  expires_at: '2026-09-01T00:00:00Z',
};

const draftPost = {
  id: 1,
  commentary: 'Borrador de prueba para LinkedIn',
  image: null,
  status: 'draft',
  scheduled_at: null,
  published_at: null,
  linkedin_post_id: '',
  error_message: '',
  created_at: '2026-07-04T10:00:00Z',
  updated_at: '2026-07-04T10:00:00Z',
};

const publishedPost = {
  ...draftPost,
  status: 'published',
  published_at: '2026-07-04T12:00:00Z',
  linkedin_post_id: 'urn:li:share:123',
};

function setupPageMock(page, {
  linkedinStatus = connectedStatus,
  posts = [draftPost],
  publishResponse = null,
} = {}) {
  // Mutable list so create/publish can update what the list returns
  const state = { posts: [...posts] };

  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'linkedin/status/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(linkedinStatus) };
    }
    if (apiPath === 'linkedin/posts/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(state.posts) };
    }
    if (apiPath === 'linkedin/posts/create/' && route.request().method() === 'POST') {
      const created = { ...draftPost, id: 99, commentary: 'Nuevo post desde E2E' };
      state.posts = [created, ...state.posts];
      return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
    }
    if (apiPath === 'linkedin/posts/1/publish/' && route.request().method() === 'POST') {
      if (publishResponse) return publishResponse;
      state.posts = [publishedPost];
      return { status: 200, contentType: 'application/json', body: JSON.stringify(publishedPost) };
    }
    return null;
  });
}

async function gotoModule(page) {
  await page.goto('/panel/linkedin');
  await page.waitForLoadState('domcontentloaded');
  await page.getByRole('heading', { name: 'LinkedIn' }).waitFor({ state: 'visible' });
}

// ─────────────────────────────────────────────
// Flow: admin-linkedin-module
// ─────────────────────────────────────────────

test.describe('Admin LinkedIn module', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8900, role: 'admin', is_staff: true } });
  });

  test('shows disconnected state with connect button', {
    tag: [...ADMIN_LINKEDIN_MODULE, '@role:admin'],
  }, async ({ page }) => {
    await setupPageMock(page, { linkedinStatus: disconnectedStatus, posts: [] });
    await gotoModule(page);

    await expect(page.getByText('LinkedIn no conectado.')).toBeVisible();
    await expect(page.getByRole('button', { name: /Conectar LinkedIn/ })).toBeVisible();
  });

  test('shows connected profile with token expiry date', {
    tag: [...ADMIN_LINKEDIN_MODULE, '@role:admin'],
  }, async ({ page }) => {
    await setupPageMock(page);
    await gotoModule(page);

    await expect(page.getByText('Gustavo Pérez')).toBeVisible();
    await expect(page.getByText(/La conexión expira el/)).toBeVisible();
  });

  test('renders posts list with status chip', {
    tag: [...ADMIN_LINKEDIN_MODULE, '@role:admin'],
  }, async ({ page }) => {
    await setupPageMock(page);
    await gotoModule(page);

    await expect(page.getByText('Borrador de prueba para LinkedIn')).toBeVisible();
    await expect(page.getByText('Borrador', { exact: true })).toBeVisible();
  });

  test('create modal saves a draft and refreshes the list', {
    tag: [...ADMIN_LINKEDIN_MODULE, '@role:admin'],
  }, async ({ page }) => {
    await setupPageMock(page, { posts: [] });
    await gotoModule(page);

    await page.getByRole('button', { name: 'Nuevo post' }).click();
    await page.getByPlaceholder(/Escribe el contenido para LinkedIn/).fill('Nuevo post desde E2E');
    await page.getByRole('button', { name: 'Guardar', exact: true }).click();

    await expect(page.getByText('Post guardado.')).toBeVisible();
    await expect(page.getByText('Nuevo post desde E2E')).toBeVisible();
  });

  test('publish now with confirm flips post to published', {
    tag: [...ADMIN_LINKEDIN_MODULE, '@role:admin'],
  }, async ({ page }) => {
    await setupPageMock(page);
    await gotoModule(page);

    await page.getByRole('button', { name: 'Publicar ahora' }).click();
    // Confirm modal
    await page.getByRole('button', { name: 'Publicar', exact: true }).click();

    await expect(page.getByText('Publicado en LinkedIn correctamente.')).toBeVisible();
    // Scope to tbody: "Publicado" also matches the table column header
    await expect(page.locator('tbody').getByText('Publicado', { exact: true })).toBeVisible();
  });

  test('publish API failure surfaces inline error', {
    tag: [...ADMIN_LINKEDIN_MODULE, '@role:admin'],
  }, async ({ page }) => {
    await setupPageMock(page, {
      publishResponse: {
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'LinkedIn API error (500): boom' }),
      },
    });
    await gotoModule(page);

    await page.getByRole('button', { name: 'Publicar ahora' }).click();
    await page.getByRole('button', { name: 'Publicar', exact: true }).click();

    await expect(page.getByText(/LinkedIn API error/)).toBeVisible();
  });
});
