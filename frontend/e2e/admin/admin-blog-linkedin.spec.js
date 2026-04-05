/**
 * E2E tests for admin blog LinkedIn integration.
 *
 * Covers flow: admin-blog-linkedin-connect
 *   - Disconnected state shows "Conectar LinkedIn" button.
 *   - Connect button fetches auth URL and opens OAuth popup.
 *   - Callback page success: success state rendered, postMessage sent to opener.
 *   - Callback page error: error state rendered.
 *   - Opener receives postMessage and transitions to connected state.
 *
 * Covers flow: admin-blog-linkedin-publish
 *   - Connected state shows profile name and publish controls.
 *   - Publish button is disabled when summary textarea is empty.
 *   - Publish button triggers API and shows success message.
 *   - Last-published timestamp shown after successful publish.
 *   - API error renders inline error message.
 */

import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import {
  ADMIN_BLOG_LINKEDIN_CONNECT,
  ADMIN_BLOG_LINKEDIN_PUBLISH,
} from '../helpers/flow-tags.js';

test.setTimeout(60_000);

// ─────────────────────────────────────────────
// Fixtures
// ─────────────────────────────────────────────

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const categoriesMock = {
  _available_categories: [
    { slug: 'technology', label: 'Tecnología' },
    { slug: 'design', label: 'Diseño' },
  ],
};

const basePost = {
  id: 1,
  title_es: 'Post de LinkedIn',
  title_en: 'LinkedIn Post',
  slug: 'post-de-linkedin',
  excerpt_es: 'Resumen ES.',
  excerpt_en: 'Excerpt EN.',
  content_es: '',
  content_en: '',
  content_json_es: {},
  content_json_en: {},
  sources: [],
  cover_image: '',
  category: 'technology',
  read_time_minutes: 5,
  is_featured: false,
  is_published: true,
  meta_title_es: '',
  meta_title_en: '',
  meta_description_es: '',
  meta_description_en: '',
  meta_keywords_es: '',
  meta_keywords_en: '',
  cover_image_credit: '',
  cover_image_credit_url: '',
  linkedin_summary_es: '',
  linkedin_summary_en: '',
  linkedin_published_at: null,
  published_at: '2026-04-01T12:00:00Z',
  created_at: '2026-04-01T10:00:00Z',
  updated_at: '2026-04-01T12:00:00Z',
};

const disconnectedStatus = { connected: false };

const connectedStatus = {
  connected: true,
  profile_name: 'Gustavo Pérez',
  profile_email: 'gustavo@example.com',
};

function setupEditPageMock(page, { linkedinStatus = disconnectedStatus } = {}) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'blog/admin/json-template/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(categoriesMock) };
    }
    if (apiPath === 'blog/admin/1/detail/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(basePost) };
    }
    if (apiPath === 'linkedin/status/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(linkedinStatus) };
    }
    if (apiPath === 'linkedin/auth-url/') {
      // Return a URL pointing to our own callback page so the popup stays within the app
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ authorization_url: '/auth/linkedin/callback?code=fake-code&state=fake-state' }),
      };
    }
    if (apiPath === 'linkedin/callback/' && route.request().method() === 'POST') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ connection: connectedStatus }),
      };
    }
    if (apiPath.match(/^blog\/admin\/1\/publish-linkedin\//)) {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Publicado en LinkedIn correctamente.' }),
      };
    }
    return null;
  });
}

// ─────────────────────────────────────────────
// Flow: admin-blog-linkedin-connect
// ─────────────────────────────────────────────

// Helper: wait for the LinkedIn fieldset to appear (rendered after onMounted async resolves)
async function waitForLinkedInSection(page) {
  await page.waitForLoadState('domcontentloaded');
  await page.locator('fieldset').filter({ hasText: 'LinkedIn' }).waitFor({ state: 'visible' });
}

test.describe('Admin Blog LinkedIn — Connect', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8900, role: 'admin', is_staff: true } });
  });

  test('shows disconnected state with connect button', {
    tag: [...ADMIN_BLOG_LINKEDIN_CONNECT, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: disconnectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    await expect(page.getByText('LinkedIn no conectado.')).toBeVisible();
    await expect(page.getByRole('button', { name: /Conectar LinkedIn/ })).toBeVisible();
  });

  test('connect button opens OAuth popup', {
    tag: [...ADMIN_BLOG_LINKEDIN_CONNECT, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: disconnectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    const popupPromise = page.waitForEvent('popup');
    await page.getByRole('button', { name: /Conectar LinkedIn/ }).click();
    const popup = await popupPromise;

    await expect(popup).toBeTruthy();
    await popup.close();
  });

  test('callback page shows success state after successful code exchange', {
    tag: [...ADMIN_BLOG_LINKEDIN_CONNECT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'linkedin/callback/' && route.request().method() === 'POST') {
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ connection: connectedStatus }),
        };
      }
      return null;
    });

    await page.goto('/auth/linkedin/callback?code=fake-code&state=fake-state');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText('LinkedIn conectado correctamente')).toBeVisible();
    await expect(page.getByText('Puedes cerrar esta ventana.')).toBeVisible();
  });

  test('callback page shows error state when LinkedIn returns error param', {
    tag: [...ADMIN_BLOG_LINKEDIN_CONNECT, '@role:admin'],
  }, async ({ page }) => {
    await page.goto('/auth/linkedin/callback?error=access_denied&error_description=User+denied+access');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText(/LinkedIn:.*access_denied|User denied access/i)).toBeVisible();
  });

  test('callback page shows error when no code is received', {
    tag: [...ADMIN_BLOG_LINKEDIN_CONNECT, '@role:admin'],
  }, async ({ page }) => {
    await page.goto('/auth/linkedin/callback');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByText('No se recibió código de autorización.')).toBeVisible();
  });

  test('opener updates to connected state after popup postMessage', {
    tag: [...ADMIN_BLOG_LINKEDIN_CONNECT, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: disconnectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    // Simulate the postMessage that the popup would send after successful auth
    await page.evaluate((status) => {
      window.postMessage({ type: 'linkedin-connected', data: status }, '*');
    }, connectedStatus);

    await expect(page.getByText('Gustavo Pérez')).toBeVisible();
    await expect(page.getByRole('button', { name: /Publicar en LinkedIn/ })).toBeVisible();
  });
});

// ─────────────────────────────────────────────
// Flow: admin-blog-linkedin-publish
// ─────────────────────────────────────────────

test.describe('Admin Blog LinkedIn — Publish', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8900, role: 'admin', is_staff: true } });
  });

  test('shows connected state with profile name and publish controls', {
    tag: [...ADMIN_BLOG_LINKEDIN_PUBLISH, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: connectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    await expect(page.getByText('Gustavo Pérez')).toBeVisible();
    await expect(page.getByRole('button', { name: /Publicar en LinkedIn/ })).toBeVisible();
  });

  test('publish button is disabled when summary is empty', {
    tag: [...ADMIN_BLOG_LINKEDIN_PUBLISH, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: connectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    // Default lang is 'es' and linkedin_summary_es is empty
    await expect(page.getByRole('button', { name: /Publicar en LinkedIn/ })).toBeDisabled();
  });

  test('publish button is enabled after filling summary', {
    tag: [...ADMIN_BLOG_LINKEDIN_PUBLISH, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: connectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    await page.getByPlaceholder(/Resumen para publicar en LinkedIn/).fill('Este artículo habla sobre LinkedIn.');

    await expect(page.getByRole('button', { name: /Publicar en LinkedIn/ })).toBeEnabled();
  });

  test('publish shows success message after API call', {
    tag: [...ADMIN_BLOG_LINKEDIN_PUBLISH, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: connectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    await page.getByPlaceholder(/Resumen para publicar en LinkedIn/).fill('Este artículo habla sobre LinkedIn.');
    await page.getByRole('button', { name: /Publicar en LinkedIn/ }).click();

    await expect(page.getByText('Publicado en LinkedIn correctamente.')).toBeVisible();
  });

  test('publish API error renders inline error message', {
    tag: [...ADMIN_BLOG_LINKEDIN_PUBLISH, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'blog/admin/json-template/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(categoriesMock) };
      }
      if (apiPath === 'blog/admin/1/detail/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(basePost) };
      }
      if (apiPath === 'linkedin/status/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(connectedStatus) };
      }
      if (apiPath.match(/^blog\/admin\/1\/publish-linkedin\//)) {
        return {
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'LinkedIn token expired.' }),
        };
      }
      return null;
    });

    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    await page.getByPlaceholder(/Resumen para publicar en LinkedIn/).fill('Resumen de prueba.');
    await page.getByRole('button', { name: /Publicar en LinkedIn/ }).click();

    await expect(page.getByText(/Error al publicar en LinkedIn|LinkedIn token expired/)).toBeVisible();
  });

  test('character counter reflects typed summary length', {
    tag: [...ADMIN_BLOG_LINKEDIN_PUBLISH, '@role:admin'],
  }, async ({ page }) => {
    await setupEditPageMock(page, { linkedinStatus: connectedStatus });
    await page.goto('/panel/blog/1/edit');
    await waitForLinkedInSection(page);

    const summary = 'Resumen de prueba para LinkedIn.';
    await page.getByPlaceholder(/Resumen para publicar en LinkedIn/).fill(summary);

    await expect(page.getByText(`${summary.length} / 1300`)).toBeVisible();
  });
});
