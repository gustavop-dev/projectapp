/**
 * E2E tests for admin hour-package creation.
 *
 * Covers: form render with derived currency, nationality preselected from
 * the query param, fill and submit, backend validation errors shown per field.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_HOUR_PACKAGES_CREATE } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
const createdPackage = { id: 10, nationality: 'EXT', currency: 'USD', name_es: 'Paquete Pro EXT', name_en: 'Pro Pack EXT', hours: 60, hourly_rate: '40.00', discount_percent: 10, is_active: true, order: 2 };

function setupMock(page, { createStatus = 201, createBody = createdPackage } = {}) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'hour-packages/admin/create/' && route.request().method() === 'POST') {
      return { status: createStatus, contentType: 'application/json', body: JSON.stringify(createBody) };
    }
    if (apiPath === 'hour-packages/admin/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
}

test.describe('Admin Hour Packages Create', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9500, role: 'admin', is_staff: true } });
  });

  test('preselects nationality from query param and shows derived currency', {
    tag: [...ADMIN_HOUR_PACKAGES_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/hour-packages/create?nationality=EXT');

    await expect(page.getByLabel('Nacionalidad')).toHaveValue('EXT');
    await expect(page.getByText('USD (derivada de la nacionalidad)')).toBeVisible();
  });

  test('fills the form, shows the computed preview and submits', {
    tag: [...ADMIN_HOUR_PACKAGES_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/hour-packages/create?nationality=EXT');

    await page.getByLabel('Nombre (ES)').fill('Paquete Pro EXT');
    await page.getByLabel('Name (EN)').fill('Pro Pack EXT');
    await page.getByLabel('Horas').fill('60');
    await page.getByLabel(/Tarifa por hora/).fill('40');
    await page.getByLabel('Descuento (%)').fill('10');

    await expect(page.getByText('Tarifa efectiva:')).toContainText('$36 USD');
    await expect(page.getByText('Total del paquete:')).toContainText('$2,160 USD');

    await page.getByRole('button', { name: 'Crear paquete' }).click();

    await expect(page).toHaveURL(/\/panel\/hour-packages$/);
  });

  test('shows per-field backend validation errors', {
    tag: [...ADMIN_HOUR_PACKAGES_CREATE, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page, {
      createStatus: 400,
      createBody: { hours: ['Las horas deben ser al menos 1.'] },
    });
    await page.goto('/panel/hour-packages/create');

    await page.getByLabel('Nombre (ES)').fill('X');
    await page.getByLabel('Name (EN)').fill('X');
    await page.getByLabel('Horas').fill('1');
    await page.getByLabel(/Tarifa por hora/).fill('100');
    await page.getByRole('button', { name: 'Crear paquete' }).click();

    await expect(page.getByText('Las horas deben ser al menos 1.')).toBeVisible();
    await expect(page.getByText('No se pudo crear el paquete. Revisa los campos.')).toBeVisible();
  });
});
