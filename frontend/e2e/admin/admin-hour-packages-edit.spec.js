/**
 * E2E tests for admin hour-package editing.
 *
 * Covers: form prefilled from detail endpoint, editing rate/discount updates
 * the computed preview, PATCH submit navigates back to the list.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_HOUR_PACKAGES_EDIT } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const packageDetail = {
  id: 3,
  nationality: 'EXT',
  currency: 'USD',
  name_es: 'Paquete Ágil EXT',
  name_en: 'Agile Pack EXT',
  note_es: 'Nota ES',
  note_en: 'Note EN',
  hours: 20,
  hourly_rate: '45.00',
  discount_percent: 0,
  is_active: true,
  order: 1,
  created_at: '2026-07-01T10:00:00Z',
  updated_at: '2026-07-01T10:00:00Z',
};

function setupMock(page, { patched = {} } = {}) {
  let lastPatchBody = null;
  const mocked = mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'hour-packages/admin/3/detail/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(packageDetail) };
    }
    if (apiPath === 'hour-packages/admin/3/update/' && route.request().method() === 'PATCH') {
      lastPatchBody = route.request().postDataJSON();
      return {
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...packageDetail, ...lastPatchBody, ...patched }),
      };
    }
    if (apiPath === 'hour-packages/admin/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    return null;
  });
  return { mocked, getLastPatchBody: () => lastPatchBody };
}

test.describe('Admin Hour Packages Edit', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 9600, role: 'admin', is_staff: true } });
  });

  test('prefills the form from the detail endpoint', {
    tag: [...ADMIN_HOUR_PACKAGES_EDIT, '@role:admin'],
  }, async ({ page }) => {
    setupMock(page);
    await page.goto('/panel/hour-packages/3/edit');

    await expect(page.getByLabel('Nombre (ES)')).toHaveValue('Paquete Ágil EXT');
    await expect(page.getByLabel('Nacionalidad')).toHaveValue('EXT');
    await expect(page.getByLabel('Horas')).toHaveValue('20');
    await expect(page.getByLabel(/Tarifa por hora/)).toHaveValue('45');
    await expect(page.getByText('USD (derivada de la nacionalidad)')).toBeVisible();
  });

  test('edits rate and discount, preview recalculates, and PATCH is sent', {
    tag: [...ADMIN_HOUR_PACKAGES_EDIT, '@role:admin'],
  }, async ({ page }) => {
    const { getLastPatchBody } = setupMock(page);
    await page.goto('/panel/hour-packages/3/edit');

    await expect(page.getByLabel(/Tarifa por hora/)).toHaveValue('45');
    await page.getByLabel(/Tarifa por hora/).fill('50');
    await page.getByLabel('Descuento (%)').fill('10');

    await expect(page.getByText('Tarifa efectiva:')).toContainText('$45 USD');
    await expect(page.getByText('Total del paquete:')).toContainText('$900 USD');

    await page.getByRole('button', { name: 'Guardar cambios' }).click();

    await expect(page).toHaveURL(/\/panel\/hour-packages$/);
    expect(getLastPatchBody()).toMatchObject({ hourly_rate: 50, discount_percent: 10 });
  });
});
