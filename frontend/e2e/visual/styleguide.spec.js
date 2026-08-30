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
import { PANEL_VIEWPORTS } from '../../config/responsive.js';

const STYLEGUIDE_URL = '/panel/styleguide';
const HEADING = 'Design System — Styleguide';

// Nuxt compiles this unusually large reference page on first request. Serial
// execution prevents five cold viewport requests from racing the dev server.
test.describe.configure({ mode: 'serial' });

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
    await page.getByTestId('base-modal-actions').getByRole('button', { name: 'Cancelar' }).click();
    await expect(page.getByRole('heading', { name: 'Demo modal' })).not.toBeVisible();
  });

  test('light mode', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@visual', '@outcome:display'],
  }, async ({ page }) => {
    await seedTheme(page, 'light');
    await page.goto(STYLEGUIDE_URL, { waitUntil: 'domcontentloaded' });

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
    await page.goto(STYLEGUIDE_URL, { waitUntil: 'domcontentloaded' });

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
 * Geometry, not pixels. The fixtures exercise the three guarantees independently:
 * short labels stay atomic, explicitly long labels share a fallback band, and a
 * companion action aligns with the control instead of the complete field block.
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

  test('keeps shared form bands level across labels, help and companion actions', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — the styleguide is a static
    // reference page; what is asserted is the laid-out geometry of the row)
    // quality: allow-deep-link (the styleguide has no in-app entry point)
    await page.goto(STYLEGUIDE_URL, { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('styleguide-form-rows')).toBeVisible();

    const atomicRow = page.getByTestId('sg-row-atomic');
    const fallbackRow = page.getByTestId('sg-row-wrapped-fallback');

    const nitLabel = atomicRow.getByText('C.C. / NIT', { exact: true });
    const billingCodeLabel = atomicRow.getByText('Código de facturación', { exact: true });
    await expect(nitLabel).toHaveCSS('white-space', 'nowrap');
    await expect(billingCodeLabel).toHaveCSS('white-space', 'nowrap');

    const oneA = await page.getByTestId('sg-row-one-a').boundingBox();
    const oneB = await page.getByTestId('sg-row-one-b').boundingBox();
    expect(Math.abs(oneA.y - oneB.y)).toBeLessThanOrEqual(1);

    const help = await page.getByTestId('sg-row-help').boundingBox();
    expect(help.y).toBeGreaterThan(oneA.y + oneA.height);
    expect(help.x).toBeLessThanOrEqual(oneA.x + 1);
    expect(help.x + help.width).toBeGreaterThanOrEqual(oneB.x + oneB.width - 1);

    const accountNameLabel = fallbackRow.getByText(
      'Nombre completo que aparecerá en la cuenta de cobro',
      { exact: true },
    );
    const accountRecipientLabel = fallbackRow.getByText(
      'Correo destinatario que recibirá la cuenta de cobro',
      { exact: true },
    );
    const fallbackA = await accountNameLabel.boundingBox();
    const fallbackB = await accountRecipientLabel.boundingBox();
    expect(fallbackA.height).toBeGreaterThan(20);
    expect(fallbackB.height).toBeGreaterThan(20);

    const rowA = await page.getByTestId('sg-row-both-a').boundingBox();
    const rowB = await page.getByTestId('sg-row-both-b').boundingBox();
    expect(Math.abs(rowA.y - rowB.y)).toBeLessThanOrEqual(1);

    const actionInput = await page.getByTestId('sg-row-action-input').boundingBox();
    const actionButton = await page.getByTestId('sg-row-action-button').boundingBox();
    const inputCenter = actionInput.y + (actionInput.height / 2);
    const buttonCenter = actionButton.y + (actionButton.height / 2);
    expect(Math.abs(inputCenter - buttonCenter)).toBeLessThanOrEqual(1);
  });

  test('keeps four-digit counts and status chips atomic', {
    tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (display flow — this asserts component geometry)
    // quality: allow-deep-link (the styleguide is the executable contract)
    await page.goto(STYLEGUIDE_URL, { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });

    const segmentedCounts = page.getByTestId('sg-segmented-counts');
    const allTab = segmentedCounts.getByRole('tab', { name: 'Todos (9999)', exact: true });
    const expectedTab = segmentedCounts.getByRole('tab', { name: 'Esperados (9999)', exact: true });
    const liquidTab = segmentedCounts.getByRole('tab', { name: 'Líquidos (9999)', exact: true });
    await expect(allTab).toHaveText('Todos (9999)');
    await expect(expectedTab).toHaveText('Esperados (9999)');
    await expect(liquidTab).toHaveText('Líquidos (9999)');
    await expect(allTab).toHaveCSS('white-space', 'nowrap');
    await expect(expectedTab).toHaveCSS('white-space', 'nowrap');
    await expect(liquidTab).toHaveCSS('white-space', 'nowrap');
    const allBox = await allTab.boundingBox();
    const expectedBox = await expectedTab.boundingBox();
    const liquidBox = await liquidTab.boundingBox();
    expect(Math.round(allBox.height)).toBe(Math.round(expectedBox.height));
    expect(Math.round(expectedBox.height)).toBe(Math.round(liquidBox.height));

    const stateBadge = page.getByTestId('sg-atomic-state-badge');
    await expect(stateBadge).toHaveCSS('white-space', 'nowrap');
    const badgeMetrics = await stateBadge.evaluate((element) => ({
      clientHeight: element.clientHeight,
      scrollHeight: element.scrollHeight,
    }));
    expect(badgeMetrics.scrollHeight).toBeLessThanOrEqual(badgeMetrics.clientHeight + 1);
  });
});

/**
 * The reference widths are product inputs, not Playwright defaults. This
 * matrix keeps the executable examples, navigation shell and max-width
 * contract aligned at every device PA-75 names explicitly.
 */
test.describe('responsive foundations at the five reference widths', () => {
  test.setTimeout(60_000);
  test.use({ hasTouch: true });

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 8402, role: 'admin', is_staff: true },
    });
    await stubPanelApi(page);
    await seedTheme(page, 'light');
  });

  for (const [profile, viewport] of Object.entries(PANEL_VIEWPORTS)) {
    test(`${profile} renders the canonical panel behavior`, {
      tag: ['@flow:admin-styleguide', '@module:admin', '@priority:P3', '@role:admin', '@outcome:display'],
    }, async ({ page }) => {
      await page.setViewportSize(viewport);
      // quality: allow-deep-link (the styleguide is the executable contract)
      await page.goto(STYLEGUIDE_URL, { waitUntil: 'domcontentloaded' });
      await expect(page.getByRole('heading', { name: HEADING })).toBeVisible({ timeout: 15_000 });
      await expect(page.locator(`[data-responsive-profile="${profile}"]`)).toBeVisible();

      const compactNavigation = viewport.width < 1000;
      await expect(page.locator('.mobile-topbar'))[
        compactNavigation ? 'toBeVisible' : 'toBeHidden'
      ]();
      await expect(page.locator('aside').first())[
        compactNavigation ? 'toBeHidden' : 'toBeVisible'
      ]();

      const tabsExample = page.getByTestId('responsive-tabs-example');
      const moduleSelect = tabsExample.locator('select').first();
      const moduleStrip = tabsExample.getByRole('tablist').first();
      await expect(moduleSelect)[compactNavigation ? 'toBeVisible' : 'toBeHidden']();
      await expect(moduleStrip)[compactNavigation ? 'toBeHidden' : 'toBeVisible']();
      await expect(tabsExample.getByTestId('filter-tabs-strip'))[
        compactNavigation ? 'toBeHidden' : 'toBeVisible'
      ]();

      const tableExample = page.getByTestId('responsive-table-example');
      if (profile === 'compact') {
        await expect(tableExample.getByTestId('responsive-group-compact').first()).toBeVisible();
      } else if (profile === 'portrait') {
        await expect(tableExample.getByTestId('responsive-group-portrait').first()).toBeVisible();
      }

      // A touch-only device can discover the same actions: no hover is needed,
      // and both the trigger and its first item keep the 44px target.
      const rowActions = page.getByRole('button', { name: 'Acciones de fila' });
      const triggerBox = await rowActions.boundingBox();
      expect(triggerBox.height).toBeGreaterThanOrEqual(44);
      await rowActions.click();
      const firstAction = page.getByRole('menuitem').first();
      await expect(firstAction).toBeVisible();
      // The dropdown itself scales from 95% during its 100ms entrance; assert
      // the stable CSS hit target instead of sampling a fractional transition
      // frame from boundingBox().
      await expect(firstAction).toHaveCSS('min-height', '44px');

      const shellBox = await page.getByTestId('panel-content-shell').boundingBox();
      expect(shellBox.width).toBeLessThanOrEqual(1441);
      const pageWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      expect(pageWidth).toBeLessThanOrEqual(viewport.width);
    });
  }
});
