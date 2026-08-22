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

  test('exposes the responsive foundation', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@outcome:display', '@responsive:foundation'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the styleguide is the direct acceptance surface)
    await seedTheme(page, 'light');
    await page.goto(STYLEGUIDE_URL, { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });

    await page.getByRole('button', { name: 'Abrir modal', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Demo modal' })).toBeVisible();
    await page.getByRole('button', { name: 'Cancelar' }).click();
    await expect(page.getByRole('heading', { name: 'Demo modal' })).not.toBeVisible();
  });

  test('light mode', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@visual', '@outcome:display'],
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

    // quality: disable wait_for_timeout (CSS token transitions need 150ms to settle before pixel-accurate screenshot)
    await page.waitForTimeout(150);

    // Allow small anti-aliasing / font-rendering noise on full-page screenshots.
    await expect(page).toHaveScreenshot('styleguide-light.png', { fullPage: true, maxDiffPixelRatio: 0.02 });
  });

  test('dark mode', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@visual', '@outcome:display'],
  }, async ({ page }) => {
    // Start from light so the layout toggle click is the explicit user
    // gesture exercising `useDarkMode().toggle()`.
    await seedTheme(page, 'light');
    await page.goto(STYLEGUIDE_URL);

    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });

    await page.getByRole('button', { name: 'Cambiar a modo oscuro' }).click();

    const html = page.locator('html');
    await expect(html).toHaveClass(/(^|\s)dark(\s|$)/);

    // quality: disable wait_for_timeout (CSS token transitions need 150ms to settle before pixel-accurate screenshot)
    await page.waitForTimeout(150);

    // Allow small anti-aliasing / font-rendering noise on full-page screenshots.
    await expect(page).toHaveScreenshot('styleguide-dark.png', { fullPage: true, maxDiffPixelRatio: 0.02 });
  });
});

/**
 * Geometry, not pixels. The styleguide carries the only `BaseFormRow` fixture
 * narrow enough to force the labels to wrap on demand, which is what lets us
 * check the two cases a real form cannot produce side by side: one label
 * wrapping, and both wrapping. A pixel snapshot would catch the regression too,
 * but it could not say *why* it changed.
 */
test.describe('styleguide form rows', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8401, role: 'admin', is_staff: true },
    });
    await stubPanelApi(page);
    await seedTheme(page, 'light');
  });

  test('keeps the controls level whether one label wraps or both do', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — the styleguide is a static
    // reference page; what is asserted is the laid-out geometry of the row)
    // quality: allow-deep-link (the styleguide has no in-app entry point)
    await page.goto(STYLEGUIDE_URL);
    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('styleguide-form-rows')).toBeVisible();

    const oneRow = page.getByTestId('sg-row-one-wrapped');
    const bothRow = page.getByTestId('sg-row-both-wrapped');

    // Row 1 — one label on a single line, the other wrapped, and only the first
    // field carrying a hint. The short label sets the single-line reference.
    const short = await oneRow.getByText('C.C. / NIT (opcional)', { exact: true }).boundingBox();
    const wrapped = await oneRow
      .getByText('Código de facturación (opcional)', { exact: true }).boundingBox();
    expect(wrapped.height).toBeGreaterThan(short.height);

    const oneA = await page.getByTestId('sg-row-one-a').boundingBox();
    const oneB = await page.getByTestId('sg-row-one-b').boundingBox();
    expect(Math.abs(oneA.y - oneB.y)).toBeLessThanOrEqual(1);

    // Row 2 — both labels wrapped: the band is as tall as the taller of the two
    // and neither control drifts.
    const bothA = await bothRow.getByText('Nombre en la cuenta de cobro', { exact: true }).boundingBox();
    const bothB = await bothRow
      .getByText('Código de facturación (opcional)', { exact: true }).boundingBox();
    expect(bothA.height).toBeGreaterThan(short.height);
    expect(bothB.height).toBeGreaterThan(short.height);

    const rowA = await page.getByTestId('sg-row-both-a').boundingBox();
    const rowB = await page.getByTestId('sg-row-both-b').boundingBox();
    expect(Math.abs(rowA.y - rowB.y)).toBeLessThanOrEqual(1);
  });
});
