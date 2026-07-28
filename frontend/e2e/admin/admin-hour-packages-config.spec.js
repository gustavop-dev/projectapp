/**
 * E2E tests for the hour-packages Configuración section — base rates.
 *
 * Covers: base-rate inputs prefilled from settings, saving propagates the
 * rate (PATCH + success notification + refreshed catalog), invalid rate is
 * rejected client-side.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_HOUR_PACKAGES_CONFIG } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const settings = {
  default_view_mode: 'table',
  base_rate_col: '30000.00',
  base_rate_ext: '18.00',
  base_rate_usa: '30.00',
  updated_at: '2026-07-01T10:00:00Z',
};

function colPackages(rate) {
  return [
    { id: 1, nationality: 'COL', currency: 'COP', name_es: 'Hora Puntual', name_en: 'Single Hour', hours: 1, hourly_rate: rate, discount_percent: 0, is_active: true, order: 1, updated_at: '2026-07-01T10:00:00Z' },
    { id: 2, nationality: 'COL', currency: 'COP', name_es: 'Paquete Ágil', name_en: 'Agile Pack', hours: 20, hourly_rate: rate, discount_percent: 10, is_active: true, order: 2, updated_at: '2026-07-01T10:00:00Z' },
  ];
}

function setupMock(page) {
  let lastPatchBody = null;
  let ratePropagated = false;
  mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'hour-packages/admin/settings/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(settings) };
    }
    if (apiPath === 'hour-packages/admin/settings/update/' && route.request().method() === 'PATCH') {
      lastPatchBody = route.request().postDataJSON();
      ratePropagated = true;
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...settings,
          base_rate_col: '35000.00',
          updated_packages: { COL: 2 },
        }),
      };
    }
    if (apiPath === 'hour-packages/admin/' && route.request().method() === 'GET') {
      const body = colPackages(ratePropagated ? '35000.00' : '30000.00');
      return { status: 200, contentType: 'application/json', body: JSON.stringify(body) };
    }
    return null;
  });
  return { getLastPatchBody: () => lastPatchBody };
}

test.describe('Admin Hour Packages Config — base rates', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9700, role: 'admin', is_staff: true } });
  });

  test('prefills the base-rate inputs from settings', {
    tag: [...ADMIN_HOUR_PACKAGES_CONFIG, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    setupMock(page);
    await page.goto('/panel/hour-packages', { waitUntil: 'domcontentloaded' });

    await page.getByTestId('hour-packages-section-config').click();

    await expect(page.getByTestId('hour-packages-base-rate-col')).toHaveValue('30000');
    await expect(page.getByTestId('hour-packages-base-rate-ext')).toHaveValue('18');
    await expect(page.getByTestId('hour-packages-base-rate-usa')).toHaveValue('30');
  });

  test('saving a new COL rate propagates and the catalog reflects it', {
    tag: [...ADMIN_HOUR_PACKAGES_CONFIG, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const { getLastPatchBody } = setupMock(page);
    await page.goto('/panel/hour-packages', { waitUntil: 'domcontentloaded' });

    await page.getByTestId('hour-packages-section-config').click();
    await page.getByTestId('hour-packages-base-rate-col').fill('35000');
    await page.getByTestId('hour-packages-save-base-rates').click();

    await expect(page.getByText('Tarifas base guardadas. 2 paquetes actualizados.')).toBeVisible();
    expect(getLastPatchBody()).toMatchObject({
      base_rate_col: 35000, base_rate_ext: 18, base_rate_usa: 30,
    });

    await page.getByTestId('hour-packages-section-catalog').click();
    await expect(page.locator('table').getByText('$35.000 COP').first()).toBeVisible();
  });

  test('shows an error notification when the settings PATCH fails server-side', {
    tag: [...ADMIN_HOUR_PACKAGES_CONFIG, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'hour-packages/admin/settings/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(settings) };
      }
      if (apiPath === 'hour-packages/admin/settings/update/' && route.request().method() === 'PATCH') {
        return { status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'boom' }) };
      }
      if (apiPath === 'hour-packages/admin/' && route.request().method() === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(colPackages('30000.00')) };
      }
      return null;
    });
    await page.goto('/panel/hour-packages', { waitUntil: 'domcontentloaded' });

    await page.getByTestId('hour-packages-section-config').click();
    await page.getByTestId('hour-packages-base-rate-col').fill('40000');
    await page.getByTestId('hour-packages-save-base-rates').click();

    await expect(page.getByText('No se pudieron guardar las tarifas base.')).toBeVisible();
  });

  test('rejects a zero rate client-side without calling the API', {
    tag: [...ADMIN_HOUR_PACKAGES_CONFIG, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    const { getLastPatchBody } = setupMock(page);
    await page.goto('/panel/hour-packages', { waitUntil: 'domcontentloaded' });

    await page.getByTestId('hour-packages-section-config').click();
    await page.getByTestId('hour-packages-base-rate-col').fill('0');
    await page.getByTestId('hour-packages-save-base-rates').click();

    await expect(page.getByText('Las tarifas base deben ser números mayores a 0.')).toBeVisible();
    expect(getLastPatchBody()).toBeNull();
  });
});
