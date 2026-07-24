/**
 * E2E tests for the admin login entry point.
 *
 * Admin authentication is Django-native: /panel/login is a static hand-off
 * page whose only job is to link out to the Django admin. There is no SPA
 * credential form to drive, so this flow is a declared abstention beyond the
 * hand-off link (see docs/USER_FLOW_MAP.md -> admin-login).
 */
import { test, expect } from '../helpers/test.js';
import { ADMIN_LOGIN } from '../helpers/flow-tags.js';

test.describe('Admin Login', () => {
  test('the login page hands off to the Django admin', {
    tag: [...ADMIN_LOGIN, '@role:admin'],
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
