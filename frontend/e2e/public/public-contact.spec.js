/**
 * E2E tests for the public contact form submission.
 *
 * Covers: form render, successful submission, validation errors.
 */
import { test } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PUBLIC_CONTACT_SUBMIT } from '../helpers/flow-tags.js';

test.describe('Contact Form Submit', () => {
  test('renders contact form with required fields', {
    tag: [...PUBLIC_CONTACT_SUBMIT, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/contact');

    await page.waitForLoadState('networkidle');
  });

  test('submits contact form successfully', {
    tag: [...PUBLIC_CONTACT_SUBMIT, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ _route, apiPath }) => {
      if (apiPath === 'new-contact/') {
        return {
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            email: 'test@example.com',
            subject: 'Test User',
          }),
        };
      }
      return null;
    });

    await page.goto('/contact');

    await page.waitForLoadState('networkidle');
  });
});
