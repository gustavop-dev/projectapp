/** Bugs caught: a missing panel entry, a broken resource partition, or a failed case request hiding its error. */
import { test, expect } from '../helpers/test.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { installMonitoringMock, monitoringCaseTitle, monitoringServerTitle } from '../helpers/monitoring.js';

test.setTimeout(60_000);

test.describe('Monitoring case list', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8400, role: 'admin', is_staff: true } });
  });

  test('opens monitoring from the panel navigation and renders the project case fixture', {
    tag: ['@flow:admin-monitoring-case-list', '@outcome:display', '@role:admin'],
  }, async ({ page }) => {
    await installMonitoringMock(page);
    await page.goto('/panel', { waitUntil: 'domcontentloaded' });
    await page.getByRole('navigation', { name: 'Navegación del panel' }).getByRole('link', { name: 'Monitoreo', exact: true }).click();

    await expect(page).toHaveURL(/\/panel\/monitoring/);
    await expect(page.getByTestId('monitoring-page').getByRole('button', { name: monitoringCaseTitle, exact: true })).toHaveCount(1);
  });

  test('switching to servers requests and shows the server case partition', {
    tag: ['@flow:admin-monitoring-case-list', '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    await installMonitoringMock(page);
    await page.goto('/panel/monitoring', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'Servers', exact: true }).click();

    await expect(page.getByRole('button', { name: monitoringServerTitle, exact: true })).toHaveCount(1);
  });

  test('shows a concrete load alert when the case request fails', {
    tag: ['@flow:admin-monitoring-case-list', '@outcome:failure', '@role:admin'],
  }, async ({ page }) => {
    await installMonitoringMock(page, { listFailure: true });
    await page.goto('/panel/monitoring', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'Refresh', exact: true }).click();

    await expect(page.getByRole('alert')).toHaveText('Could not load data. Try refreshing.');
  });
});
