/**
 * E2E tests for admin proposal manual alerts flow.
 *
 * Covers: alerts panel rendering, create alert form, dismiss alert,
 * and auto-alerts merged with manual alerts.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_MANUAL_ALERTS } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockProposals = [
  { id: 1, uuid: 'aaa', title: 'Propuesta Alpha', client_name: 'Carlos', client_email: 'c@t.com', status: 'sent', total_investment: 5000, currency: 'COP', view_count: 0, is_active: true },
  { id: 2, uuid: 'bbb', title: 'Propuesta Beta', client_name: 'Ana', client_email: 'a@t.com', status: 'draft', total_investment: 3000, currency: 'USD', view_count: 2, is_active: true },
];

const mockAlerts = [
  { id: 1, client_name: 'Carlos', title: 'Propuesta Alpha', alert_type: 'not_viewed', message: 'No ha sido vista en 3 días' },
  { id: 2, client_name: 'Ana', title: 'Propuesta Beta', alert_type: 'manual_reminder', message: 'Llamar para seguimiento', manual_alert_id: 10 },
];

const dashboardData = { total_proposals: 2, conversion_rate: 0, avg_time_to_first_view: null, avg_time_to_response: null, status_distribution: {}, top_rejection_reasons: [], monthly_trends: [], avg_value_by_status: {} };

function setupMock(page, { alerts = mockAlerts, proposals = mockProposals } = {}) {
  let currentAlerts = [...alerts];
  return mockApi(page, async ({ route, apiPath }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'proposals/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(proposals) };
    }
    if (apiPath === 'proposals/alerts/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(currentAlerts) };
    }
    if (apiPath === 'proposals/alerts/create/' && route.request().method() === 'POST') {
      const payload = route.request().postDataJSON();
      const newAlert = {
        id: proposals.find(p => p.id === payload.proposal)?.id || 1,
        client_name: proposals.find(p => p.id === payload.proposal)?.client_name || 'Test',
        title: proposals.find(p => p.id === payload.proposal)?.title || 'Test',
        alert_type: `manual_${payload.alert_type}`,
        message: payload.message,
        manual_alert_id: 99,
      };
      currentAlerts = [...currentAlerts, newAlert];
      return { status: 201, contentType: 'application/json', body: JSON.stringify(newAlert) };
    }
    if (apiPath.match(/proposals\/alerts\/\d+\/dismiss\//) && route.request().method() === 'PATCH') {
      const alertId = parseInt(apiPath.match(/alerts\/(\d+)\//)[1]);
      currentAlerts = currentAlerts.filter(a => a.manual_alert_id !== alertId);
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(dashboardData) };
    }
    return null;
  });
}

test.describe('Admin Proposal Manual Alerts', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders alerts panel with auto and manual alerts', {
    tag: [...ADMIN_PROPOSAL_MANUAL_ALERTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Propuestas que necesitan atención')).toBeVisible();
    await expect(page.getByText('No ha sido vista en 3 días')).toBeVisible();
    await expect(page.getByText('Llamar para seguimiento')).toBeVisible();
  });

  test('clicking "+ Crear recordatorio" toggles the alert creation form', {
    tag: [...ADMIN_PROPOSAL_MANUAL_ALERTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    const formToggle = page.getByText('+ Crear recordatorio');
    await expect(formToggle).toBeVisible();

    await formToggle.click();
    const messageInput = page.getByPlaceholder('Ej: Llamar al cliente para seguimiento...');
    await expect(messageInput).toBeVisible();
    await expect(page.getByRole('button', { name: 'Crear', exact: true })).toBeVisible();

    // Toggle off
    await page.getByText('Cancelar').click();
    await expect(messageInput).not.toBeVisible();
  });

  test('creating a new alert adds it to the alerts list', {
    tag: [...ADMIN_PROPOSAL_MANUAL_ALERTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    await page.getByText('+ Crear recordatorio').click();

    // Fill form
    await page.locator('select').filter({ hasText: 'Seleccionar...' }).selectOption('1');
    await page.getByPlaceholder('Ej: Llamar al cliente para seguimiento...').fill('Revisar cotización pendiente');

    await page.getByRole('button', { name: 'Crear' }).click();

    // After create, the form closes and a fresh alerts fetch happens
    await expect(page.getByText('Revisar cotización pendiente')).toBeVisible({ timeout: 10000 });
  });

  test('dismiss button removes a manual alert from the list', {
    tag: [...ADMIN_PROPOSAL_MANUAL_ALERTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await page.waitForLoadState('networkidle');

    // Manual alert has dismiss button (✕)
    const dismissBtn = page.getByTitle('Descartar');
    await expect(dismissBtn).toBeVisible();

    const [response] = await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/alerts/') && r.url().includes('dismiss')),
      dismissBtn.click(),
    ]);
    await response.finished();

    // Manual alert message should no longer be visible
    await expect(page.getByText('Llamar para seguimiento')).not.toBeVisible();
  });
});
