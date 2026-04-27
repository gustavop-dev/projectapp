/**
 * Visual regression tests for the design system styleguide.
 *
 * Captures full-page screenshots of `/panel/styleguide` in both light and
 * dark mode so accidental token / base-component changes are caught as
 * pixel diffs.
 *
 * Baseline snapshots live in
 *   `e2e/visual/styleguide.spec.js-snapshots/`
 *
 * To regenerate them after an *intentional* design change, run:
 *   npm --prefix frontend run e2e -- e2e/visual/styleguide.spec.js --update-snapshots
 *
 * Do NOT regenerate to silence a failing test that you did not mean to
 * cause — investigate the diff first.
 *
 * Implementation notes:
 *  - The admin layout drives the `dark` class on `<html>` via the
 *    `useDarkMode` composable (storage key `projectapp-dark-mode`). That is
 *    the toggle that actually changes which token values resolve. The
 *    button rendered inside `pages/panel/styleguide.vue` itself is wired to
 *    a *separate* `useDiagnosticDarkMode` composable (storage key
 *    `diagnostic_theme`) used only for in-page demos, so we do not click
 *    that button for the snapshot.
 *  - Auth: the admin-auth middleware calls `auth/check/`. We stub it via
 *    `mockApi` and seed `localStorage` with a fake JWT through
 *    `setAuthLocalStorage`, matching the pattern used by every other admin
 *    spec in this suite (`e2e/admin/admin-dashboard.spec.js`, etc.). No
 *    real login flow is needed.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';

const STYLEGUIDE_URL = '/panel/styleguide';
const HEADING = 'Design System — Styleguide';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

/**
 * Stub every backend call the panel layout / styleguide page may issue so
 * the snapshot is deterministic across environments. The styleguide page
 * itself is purely presentational — only the admin layout / `admin-auth`
 * middleware hit the API.
 */
async function stubPanelApi(page) {
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/') {
      return { status: 200, contentType: 'application/json', body: '[]' };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: '{}' };
    }
    if (apiPath === 'blog/admin/') {
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], count: 0, page: 1, page_size: 10, total_pages: 1 }),
      };
    }
    return null;
  });
}

/**
 * Force a deterministic theme before the app boots, regardless of the
 * runner's `prefers-color-scheme`. We seed both:
 *   - `projectapp-dark-mode` — the layout-level toggle that adds/removes
 *     the `dark` class on `<html>` (`composables/useDarkMode.js`).
 *   - `diagnostic_theme`     — the page-level toggle used by the
 *     styleguide demo button (`composables/useDiagnosticDarkMode.js`).
 */
async function seedTheme(page, theme /* 'light' | 'dark' */) {
  await page.addInitScript((value) => {
    const dark = value === 'dark';
    try {
      localStorage.setItem('projectapp-dark-mode', JSON.stringify(dark));
      localStorage.setItem('diagnostic_theme', dark ? 'dark' : 'light');
    } catch (_e) {
      /* ignore */
    }
  }, theme);
}

test.describe('design system styleguide visual regression', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8400, role: 'admin', is_staff: true },
    });
    await stubPanelApi(page);
  });

  test('light mode', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@visual'],
  }, async ({ page }) => {
    await seedTheme(page, 'light');
    await page.goto(STYLEGUIDE_URL);

    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });

    const html = page.locator('html');
    // Defensive: if for some reason we landed in dark mode, flip via the
    // layout toggle (which drives the `dark` class on <html>).
    if (await html.evaluate((el) => el.classList.contains('dark'))) {
      await page.getByRole('button', { name: 'Cambiar a modo claro' }).click();
    }
    await expect(html).not.toHaveClass(/(^|\s)dark(\s|$)/);

    // Let any token transitions settle.
    await page.waitForTimeout(150);

    await expect(page).toHaveScreenshot('styleguide-light.png', { fullPage: true });
  });

  test('dark mode', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@visual'],
  }, async ({ page }) => {
    // Start from light so the layout toggle click is the explicit user
    // gesture exercising `useDarkMode().toggle()`.
    await seedTheme(page, 'light');
    await page.goto(STYLEGUIDE_URL);

    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });

    await page.getByRole('button', { name: 'Cambiar a modo oscuro' }).click();

    const html = page.locator('html');
    await expect(html).toHaveClass(/(^|\s)dark(\s|$)/);

    // Let dark-mode token transitions settle before snapshotting.
    await page.waitForTimeout(150);

    await expect(page).toHaveScreenshot('styleguide-dark.png', { fullPage: true });
  });
});
