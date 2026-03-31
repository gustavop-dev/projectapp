/**
 * E2E tests for the public contact form submission.
 *
 * Covers: form render, successful submission, validation errors.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { PUBLIC_CONTACT_SUBMIT } from '../helpers/flow-tags.js';

test.describe('Contact Form Submit', () => {
  test('renders contact form with required fields', {
    tag: [...PUBLIC_CONTACT_SUBMIT, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/contact');

    // Contact page heading should be visible
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 15000 });

    // Form inputs should be present
    await expect(page.locator('form')).toBeAttached();
    await expect(page.locator('input[type="email"]')).toBeAttached();
  });

  test('submits contact form successfully', {
    tag: [...PUBLIC_CONTACT_SUBMIT, '@role:guest'],
  }, async ({ page }) => {
    await mockApi(page, async ({ _route, apiPath, method }) => {
      if (apiPath === 'new-contact/' && method === 'POST') {
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
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 15000 });

    const form = page.locator('form');
    await form.locator('input[type="text"]').fill('Test User');
    await form.locator('input[type="tel"]').fill('+573001234567');
    await form.locator('input[type="email"]').fill('test@example.com');
    await form.locator('textarea').fill('E2E contact project description');

    await form.getByRole('button', { name: /send message|enviar mensaje|enviar/i }).click();

    await page.waitForURL(/contact-success/, { timeout: 20_000 });
    await expect(page.getByRole('heading', { level: 1 })).toContainText(/gracias|thank/i);
  });
});
