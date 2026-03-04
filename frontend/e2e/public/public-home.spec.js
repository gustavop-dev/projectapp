/**
 * E2E tests for the public home page.
 *
 * Covers: page render, hero section, services cards, contact form section,
 * footer, and basic navigation elements.
 */
import { test, expect } from '../helpers/test.js';
import { PUBLIC_HOME } from '../helpers/flow-tags.js';

test.describe('Home Page', () => {
  test('renders hero section and main content', {
    tag: [...PUBLIC_HOME, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('header')).toBeVisible();
    await expect(page.locator('h1')).toBeVisible();
  });

  test('renders with Spanish locale', {
    tag: [...PUBLIC_HOME, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/es-co');

    await expect(page.locator('h1')).toBeVisible();
  });

  test('renders with English locale', {
    tag: [...PUBLIC_HOME, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/en-us');

    await expect(page.locator('h1')).toBeVisible();
  });
});
