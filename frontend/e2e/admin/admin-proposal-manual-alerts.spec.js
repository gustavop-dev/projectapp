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
  { id: 3, uuid: 'ccc', title: 'Propuesta Gamma', client_name: 'Pedro', client_email: 'p@t.com', status: 'accepted', total_investment: 9000, currency: 'USD', view_count: 5, is_active: true },
];

const mockAlerts = [
  { id: 1, client_name: 'Carlos', title: 'Propuesta Alpha', alert_type: 'not_viewed', message: 'No ha sido vista en 3 días' },
  { id: 2, client_name: 'Ana', title: 'Propuesta Beta', alert_type: 'manual_reminder', message: 'Llamar para seguimiento', manual_alert_id: 10 },
  { id: 3, client_name: 'Pedro', title: 'Propuesta Gamma', alert_type: 'manual_followup', message: 'No debería mostrarse porque está aceptada', manual_alert_id: 11 },
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

async function gotoProposalPanel(page) {
  await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('h1').filter({ hasText: /^Propuestas$/ }).first()).toBeVisible({ timeout: 30000 });
  await expect(page.getByText('Propuestas que necesitan atención')).toBeVisible({ timeout: 30000 });
}

test.describe('Admin Proposal Manual Alerts', () => {
  test.describe.configure({ timeout: 60_000 });

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
    await gotoProposalPanel(page);

    await expect(page.getByText('Propuestas que necesitan atención')).toBeVisible();
    await expect(page.getByText('No ha sido vista en 3 días')).toBeVisible();
    await expect(page.getByText('Llamar para seguimiento')).toBeVisible();
    await expect(page.getByText('No debería mostrarse porque está aceptada')).not.toBeVisible();
  });

  test('clicking "+ Crear recordatorio" toggles the alert creation form', {
    tag: [...ADMIN_PROPOSAL_MANUAL_ALERTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoProposalPanel(page);

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
    await gotoProposalPanel(page);

    await page.getByText('+ Crear recordatorio').click();

    // Fill form
    await page.locator('select').filter({ hasText: 'Seleccionar...' }).selectOption('1');
    await page.getByPlaceholder('Ej: Llamar al cliente para seguimiento...').fill('Revisar cotización pendiente');

    await Promise.all([
      page.waitForResponse(r => r.url().includes('proposals/alerts/create/') && r.request().method() === 'POST'),
      page.getByRole('button', { name: 'Crear' }).click(),
    ]);

    // Alerts are grouped by client; for same-client alerts the UI may collapse into a grouped summary.
    await expect(
      page.getByText(/Revisar cotización pendiente|2 alertas en 1 propuesta\(s\)\./)
    ).toBeVisible({ timeout: 10000 });
  });

  test('dismiss button removes a manual alert from the list', {
    tag: [...ADMIN_PROPOSAL_MANUAL_ALERTS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await gotoProposalPanel(page);

    // Dismiss the specific manual alert under test.
    // Alert cards use semantic `bg-surface` (was `bg-white` pre-design-system migration).
    const dismissBtn = page
      .getByText('Llamar para seguimiento')
      .first()
      .locator('xpath=ancestor::div[contains(@class,"bg-surface")][1]')
      .locator('button[title="Descartar"]')
      .first();
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
