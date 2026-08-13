/**
 * E2E tests for the admin login entry point and the panel session guard.
 *
 * Admin authentication is Django-native: /panel/login is a static hand-off
 * page whose only job is to link out to the Django admin. There is no SPA
 * credential form to drive, so this flow is a declared abstention beyond the
 * hand-off link (see docs/USER_FLOW_MAP.md -> admin-login).
 *
 * The second describe block covers the companion flow
 * admin-panel-session-expired: what happens when a browser without a valid
 * staff session requests a protected /panel/* route directly (middleware
 * frontend/middleware/admin-auth.js).
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { ADMIN_LOGIN, ADMIN_PANEL_SESSION_EXPIRED } from '../helpers/flow-tags.js';

test.describe('Admin Login', () => {
  test('the login page hands off to the Django admin', {
    tag: [...ADMIN_LOGIN, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (admin login is Django-native — /panel/login only
    // links out to /admin/, there is no SPA credential form to exercise; declared
    // abstention recorded in docs/USER_FLOW_MAP.md)
    // Fails if the hand-off link to the Django admin is removed or its href drifts.
    await page.goto('/panel/login', { waitUntil: 'domcontentloaded' });

    const adminLink = page.getByRole('link', { name: /Django Admin/i });
    await expect(adminLink).toHaveAttribute('href', '/admin/');
  });
});

test.describe('Admin Panel Session Guard', () => {
  test('requesting a protected panel route without a staff session hard-redirects to the Django login with next=', {
    tag: [...ADMIN_PANEL_SESSION_EXPIRED, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (this flow is triggered by a direct request
    // to a protected /panel/* route — a stale bookmark, a shared link, or a
    // browser reopened after the session cookie expired. There is no in-page
    // element to click before the admin-auth middleware's hard redirect fires;
    // page.goto() IS the user action under test, not a bypass of one.)
    // Fails if admin-auth stops redirecting on a 401/403 from /api/auth/check/
    // (letting an unauthenticated browser render the panel), or if it drops/
    // mangles the `next=` param so signing in again no longer returns the
    // admin to the page they originally requested.
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/' && method === 'GET') {
        return {
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Authentication credentials were not provided.' }),
        };
      }
      return null;
    });

    // Stub the destination, the same way this suite stubs /api/**: /admin/ is
    // proxied to Django (nuxt.config dev proxy), which only runs on a dev box.
    // Without a listener the proxy fails at the network level, Chromium cancels
    // the navigation and the URL never leaves the panel route — so the guard
    // under test would read as broken wherever Django is not up (CI included).
    await page.route('**/admin/login/**', (route) => route.fulfill({
      status: 200,
      contentType: 'text/html',
      body: '<html><body>Django admin login</body></html>',
    }));

    // Direct navigation to a protected panel page, pre-localized so the locale
    // redirect doesn't add an extra hop before the auth guard runs.
    await page.goto('/en-us/panel/proposals', { waitUntil: 'domcontentloaded' }).catch(() => {});

    // The middleware redirects with window.location.href (full page nav, not
    // navigateTo/SPA), so it lands outside the Nuxt router entirely. Assert the
    // full concrete URL — both the Django login path AND the preserved next=
    // target — so this fails if either the redirect or the `next=` value drifts.
    await expect(page).toHaveURL(/\/admin\/login\/\?next=\/en-us\/panel\/proposals$/, { timeout: 20_000 });

    const redirectUrl = new URL(page.url());
    expect(redirectUrl.searchParams.get('next')).toBe('/en-us/panel/proposals');
  });
});
