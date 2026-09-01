/**
 * Responsive accounting navigation matrix.
 *
 * R-accounting-tabs-01: a breakpoint could hide the selected accounting tab or
 * route it to the wrong surface while a single representative accounting page
 * stayed green.
 */
import { test, expect, assertResponsiveScenario } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { waitForNuxtApp } from '../helpers/navigation.js';
import { viewportUse } from '../helpers/viewports.js';
import { RESPONSIVE_PROFILES, batchForScenario, getResponsiveScenario } from './catalog-scenarios.js';

test.setTimeout(60_000);

const tabs = Object.freeze([
  { key: 'index', url: '/panel/accounting', heading: 'Resumen', flow: 'admin-accounting-dashboard', catalogKey: 'frontend/pages/panel/accounting/index.vue' },
  { key: 'pocket', url: '/panel/accounting/pocket', heading: 'Bolsillo ProjectApp', flow: 'admin-accounting-pocket', catalogKey: 'frontend/pages/panel/accounting/pocket.vue' },
  { key: 'incomes', url: '/panel/accounting/incomes', heading: 'Ingresos', flow: 'admin-accounting-income-crud', catalogKey: 'frontend/pages/panel/accounting/incomes.vue' },
  { key: 'expenses', url: '/panel/accounting/expenses', heading: 'Gastos', flow: 'admin-accounting-expenses-crud', catalogKey: 'frontend/pages/panel/accounting/expenses.vue' },
  { key: 'hostings', url: '/panel/accounting/hostings', heading: 'Hostings', flow: 'admin-accounting-hostings', catalogKey: 'frontend/pages/panel/accounting/hostings.vue' },
  { key: 'collections', url: '/panel/accounting/collections', heading: 'Cuentas de cobro', flow: 'admin-accounting-collections', catalogKey: 'frontend/pages/panel/accounting/collections.vue' },
  { key: 'recurring', url: '/panel/accounting/recurring', heading: 'Pagos recurrentes', flow: 'admin-accounting-recurring', catalogKey: 'frontend/pages/panel/accounting/recurring.vue' },
  { key: 'ads', url: '/panel/accounting/ads', heading: 'Ads', flow: 'admin-accounting-ads', catalogKey: 'frontend/pages/panel/accounting/ads.vue' },
  { key: 'cards', url: '/panel/accounting/cards', heading: 'Tarjetas', flow: 'admin-accounting-cards', catalogKey: 'frontend/pages/panel/accounting/cards.vue' },
  { key: 'statements', url: '/panel/accounting/statements', heading: 'Extractos de tarjeta', flow: 'admin-accounting-statements', catalogKey: 'frontend/pages/panel/accounting/statements.vue' },
  { key: 'history', url: '/panel/accounting/history', heading: 'Historial', flow: 'admin-accounting-history', catalogKey: 'frontend/pages/panel/accounting/history.vue' },
  { key: 'settings', url: '/panel/accounting/settings', heading: 'Configuración', flow: 'admin-accounting-settings', catalogKey: 'frontend/pages/panel/accounting/settings.vue' },
]);

async function mockAccountingNavigation(page) {
  await setAuthLocalStorage(page, {
    token: 'responsive-accounting-token',
    userAuth: { id: 9001, role: 'admin', is_staff: true, is_superuser: true },
  });
  await mockApi(page, async ({ apiPath }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true, is_superuser: true } }) };
    }
    if (apiPath.startsWith('accounts/saved-filter-tabs')) return { status: 200, contentType: 'application/json', body: '[]' };
    if (apiPath.startsWith('accounting/dashboard/')) {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ year: 2026, partners: {}, monthly: [], expected_current_month: {}, card_debt: {}, ads: {}, hostings: {} }) };
    }
    if (apiPath.startsWith('accounting/')) return { status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], meta: { balance: '0.00' } }) };
    return null;
  });
}

const subnavActionByProfile = Object.freeze({
  compact: (page, tab) => page.getByTestId('accounting-subnav-select').selectOption(tab.key),
  portrait: (page, tab) => page.getByTestId('accounting-subnav-select').selectOption(tab.key),
  landscape: (page, tab) => page.getByTestId(`accounting-subnav-${tab.key}`).click(),
  desktop: (page, tab) => page.getByTestId(`accounting-subnav-${tab.key}`).click(),
  wide: (page, tab) => page.getByTestId(`accounting-subnav-${tab.key}`).click(),
});

const subnavControlByProfile = Object.freeze({
  compact: (page) => page.getByTestId('accounting-subnav-select'),
  portrait: (page) => page.getByTestId('accounting-subnav-select'),
  landscape: (page, tab) => page.getByTestId(`accounting-subnav-${tab.key}`),
  desktop: (page, tab) => page.getByTestId(`accounting-subnav-${tab.key}`),
  wide: (page, tab) => page.getByTestId(`accounting-subnav-${tab.key}`),
});

for (const profile of RESPONSIVE_PROFILES) {
  test.describe(`accounting tabs · ${profile}`, { tag: [`@viewport:${profile}`] }, () => {
    test.use(viewportUse(profile));

    for (const tab of tabs) {
      const scenario = getResponsiveScenario(tab.catalogKey);
      const batch = batchForScenario(tab.catalogKey);
      test(`${tab.heading} stays reachable from the accounting subnav`, {
        tag: [
          `@flow:${tab.flow}`,
          '@outcome:display',
          '@responsive:accounting',
          `@responsive-scenario:${scenario.catalogKey}`,
          `@responsive-batch:${batch}`,
          `@viewport:${profile}`,
        ],
      }, async ({ page }, testInfo) => {
        // quality: allow-deep-link (the matrix setup opens the accounting hub, then the behavior under test uses its real subnav)
        await mockAccountingNavigation(page);
        await page.goto('/en-us/panel/accounting', { waitUntil: 'domcontentloaded' });
        await waitForNuxtApp(page);
        await expect(page.getByRole('heading', { name: 'Resumen', level: 1 }))
          .toBeVisible({ timeout: 45_000 });

        const subnavControl = subnavControlByProfile[profile](page, tab);
        await subnavControl.focus();
        await expect(subnavControl).toBeFocused();
        await subnavControl.press('Tab');
        await page.keyboard.press('Shift+Tab');
        await expect(subnavControl).toBeFocused();
        await subnavActionByProfile[profile](page, tab);

        await expect(page).toHaveURL(new RegExp(`${tab.url}$`));
        await expect(page.getByRole('heading', { name: tab.heading, level: 1 })).toHaveText(tab.heading);
        await assertResponsiveScenario(page, testInfo, scenario, { profile });
      });
    }
  });
}
