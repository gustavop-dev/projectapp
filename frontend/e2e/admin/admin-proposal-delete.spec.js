/**
 * E2E tests for admin proposal deletion.
 *
 * Exercises the full real-user delete flow from /panel/proposals: open the row
 * actions modal → "Eliminar" → ConfirmModal (type "DELETE") → confirm, and both
 * outcomes — success (toast + list refresh) and the 409 blocked-delete path for a
 * proposal linked to a launched project.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_DELETE } from '../helpers/flow-tags.js';

const proposal = {
  id: 1,
  uuid: '11111111-1111-1111-1111-111111111111',
  title: 'Delete Me Proposal',
  client_name: 'Delete Client',
  client_email: 'client@test.com',
  client_phone: '+573001234567',
  status: 'draft',
  language: 'es',
  total_investment: '5000000',
  currency: 'COP',
  view_count: 0,
  heat_score: 5,
  sent_at: null,
  is_active: true,
  created_at: '2026-03-01T12:00:00Z',
};

const json = (body) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

async function openDeleteConfirm(page) {
  await expect(page.getByText('Delete Client')).toBeVisible({ timeout: 15000 });
  // quality: allow-fragile-selector (row actions button has no testid — last SVG button in the table)
  await page.locator('table button').filter({ has: page.locator('svg') }).last().click();
  const actionsOverlay = page.locator('div.fixed.inset-0').filter({
    has: page.getByRole('heading', { level: 3, name: proposal.title }),
  });
  await actionsOverlay.getByText('Eliminar', { exact: true }).click();
  // ConfirmModal requires typing DELETE before the confirm button enables.
  await expect(page.getByTestId('confirm-modal-confirm')).toBeDisabled();
  await page.getByTestId('confirm-type-input').fill('DELETE');
  await expect(page.getByTestId('confirm-modal-confirm')).toBeEnabled();
}

test.describe('Admin Proposal Delete', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-admin-token', userAuth: { id: 8500, role: 'admin', is_staff: true } });
  });

  test('typing DELETE and confirming removes the proposal and shows a success toast', {
    tag: [...ADMIN_PROPOSAL_DELETE, '@role:admin'],
  }, async ({ page }) => {
    let deleted = false;
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true } });
      if (apiPath === 'proposals/dashboard/') return json({ total: 1, conversion_rate: 0 });
      if (apiPath === 'proposals/alerts/') return json([]);
      // Stateful list: after delete, refreshData() re-fetches an empty list.
      if (apiPath === 'proposals/') return json(deleted ? [] : [proposal]);
      if (apiPath === 'proposals/1/delete/' && method === 'DELETE') {
        deleted = true;
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return null;
    });

    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await openDeleteConfirm(page);

    await Promise.all([
      page.waitForResponse((r) => r.url().includes('proposals/1/delete/')),
      page.getByTestId('confirm-modal-confirm').click(),
    ]);

    await expect(page.getByText('Propuesta eliminada.')).toBeVisible();
    // refreshData() re-fetched the (now empty) list → the row is gone.
    await expect(page.getByText('Delete Client')).not.toBeVisible();
  });

  test('a 409 (project-linked) delete surfaces the backend error and keeps the row', {
    tag: [...ADMIN_PROPOSAL_DELETE, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath, method }) => {
      if (apiPath === 'auth/check/') return json({ user: { username: 'admin', is_staff: true } });
      if (apiPath === 'proposals/dashboard/') return json({ total: 1, conversion_rate: 0 });
      if (apiPath === 'proposals/alerts/') return json([]);
      if (apiPath === 'proposals/') return json([proposal]);
      if (apiPath === 'proposals/1/delete/' && method === 'DELETE') {
        return { status: 409, contentType: 'application/json', body: JSON.stringify({ error: 'La propuesta está vinculada a un proyecto lanzado.' }) };
      }
      return null;
    });

    await page.goto('/panel/proposals', { waitUntil: 'domcontentloaded' });
    await openDeleteConfirm(page);

    await Promise.all([
      page.waitForResponse((r) => r.url().includes('proposals/1/delete/')),
      page.getByTestId('confirm-modal-confirm').click(),
    ]);

    await expect(page.getByText('La propuesta está vinculada a un proyecto lanzado.')).toBeVisible();
    // Delete failed → list not refreshed, the row remains.
    await expect(page.getByText('Delete Client')).toBeVisible();
  });
});
