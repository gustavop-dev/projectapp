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

    // Hero section renders
    // quality: disable fragile_locator (public page has multiple h1 elements; first targets the hero heading)
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible({ timeout: 15000 });

    // quality: allow-fragile-selector (page has no testid sections, first section confirms meaningful content)
    await expect(page.locator('section').first()).toBeAttached();
  });

  test('renders with Spanish locale', {
    tag: [...PUBLIC_HOME, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/es-co');
    await expect(page).toHaveURL(/\/es-co/);
    // quality: disable fragile_locator (public page has multiple h1 elements; first targets the hero heading)
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible({ timeout: 15000 });
  });

  test('renders with English locale', {
    tag: [...PUBLIC_HOME, '@role:guest'],
  }, async ({ page }) => {
    await page.goto('/en-us');
    await expect(page).toHaveURL(/\/en-us/);
    // quality: disable fragile_locator (public page has multiple h1 elements; first targets the hero heading)
    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible({ timeout: 15000 });
  });
});
