/**
 * E2E tests for admin proposal batch actions.
 *
 * @flow: admin-proposal-batch-actions
 *
 * Covers: selecting proposals via checkboxes, batch action bar visibility,
 * cancel clears selection, select-all toggle, batch delete/expire/resend buttons.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_PROPOSAL_BATCH_ACTIONS } from '../helpers/flow-tags.js';

const mockProposals = [
  { id: 1, title: 'Proposal Alpha', client_name: 'Client A', client_email: 'a@test.com', email_intro: 'Esta propuesta resuelve la dispersión de Client A para acelerar su operación.', status: 'sent', total_investment: '5000000', currency: 'COP', view_count: 3, heat_score: 5, is_active: true },
  { id: 2, title: 'Proposal Beta', client_name: 'Client B', client_email: 'b@test.com', email_intro: 'Esta propuesta automatiza el seguimiento para que Client B reduzca errores.', status: 'viewed', total_investment: '8000000', currency: 'COP', view_count: 7, heat_score: 8, is_active: true },
  { id: 3, title: 'Proposal Gamma', client_name: 'Client C', client_email: 'c@test.com', status: 'draft', total_investment: '3000000', currency: 'COP', view_count: 0, heat_score: 0, is_active: true },
];

function setupMock(page) {
  return mockApi(page, async ({ apiPath, route }) => {
    if (apiPath === 'auth/check/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
    }
    if (apiPath === 'proposals/' && route.request().method() === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
    }
    if (apiPath === 'proposals/dashboard/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: 3, by_status: {}, conversion_rate: 0, avg_close_days: 0 }) };
    }
    if (apiPath === 'proposals/alerts/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === 'proposals/bulk-action/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify({ affected: 2, action: 'delete' }) };
    }
    return null;
  });
}

test.describe('Batch Actions on Proposals', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8000, role: 'admin', is_staff: true } });
  });

  test('action bar is hidden when no proposals selected', {
    tag: ['@outcome:display', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');

    // Table should render
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    // Batch bar should NOT be visible (no selections)
    await expect(page.getByTestId('batch-action-bar')).not.toBeVisible();
  });

  test('selecting a checkbox shows the bulk action bar', {
    tag: ['@outcome:display', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('proposal-select-1').check();

    // Batch bar should appear with count
    await expect(page.getByText('1 seleccionado')).toBeVisible({ timeout: 5000 });
  });

  test('bulk action bar shows resend, expire, delete, and cancel buttons', {
    tag: ['@outcome:display', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('proposal-select-1').check();

    // Scope assertions to the canonical sticky batch bar and its menu.
    const batchBar = page.getByTestId('batch-action-bar');
    await expect(batchBar).toBeVisible({ timeout: 5000 });
    await batchBar.getByRole('button', { name: /Acciones/ }).click();
    await expect(batchBar.getByRole('menuitem', { name: /Re-enviar/ })).toBeVisible();
    await expect(batchBar.getByRole('menuitem', { name: /Expirar/ })).toBeVisible();
    await expect(batchBar.getByRole('menuitem', { name: /Eliminar/ })).toBeVisible();
    await expect(batchBar.getByRole('button', { name: /Cancelar/ })).toBeVisible();
  });

  test('cancel button clears selection and hides action bar', {
    tag: ['@outcome:display', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('proposal-select-1').check();
    await expect(page.getByText('1 seleccionado')).toBeVisible({ timeout: 5000 });

    // Click cancel
    await page.getByRole('button', { name: /Cancelar/ }).click();

    // Bar should hide
    await expect(page.getByTestId('batch-action-bar')).not.toBeVisible({ timeout: 5000 });
  });

  // Catches: a bulk-delete button that's visually present but not wired, or
  // that submits the wrong id set — previously nothing ever clicked it even
  // though the mock bulk-action handler has sat unused since it was added.
  test('clicking Eliminar sends the bulk delete request with the selected ids and clears selection', {
    tag: ['@outcome:success', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    let bulkActionBody = null;
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/' && route.request().method() === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockProposals) };
      }
      if (apiPath === 'proposals/dashboard/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: 3, by_status: {}, conversion_rate: 0, avg_close_days: 0 }) };
      }
      if (apiPath === 'proposals/alerts/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === 'proposals/bulk-action/' && route.request().method() === 'POST') {
        bulkActionBody = route.request().postDataJSON();
        return {
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ affected: bulkActionBody.ids.length, action: bulkActionBody.action }),
        };
      }
      return null;
    });
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('proposal-select-1').check();
    await page.getByTestId('proposal-select-2').check();
    await expect(page.getByText('2 seleccionados')).toBeVisible({ timeout: 5000 });

    const batchBar = page.getByTestId('batch-action-bar');
    await batchBar.getByRole('button', { name: /Acciones/ }).click();
    await batchBar.getByRole('menuitem', { name: /Eliminar/ }).click();

    // Deleting proposals routes through the shared confirm modal.
    await page.getByTestId('confirm-modal-confirm').click();

    await expect.poll(() => bulkActionBody, { timeout: 5000 }).not.toBeNull();
    expect([...bulkActionBody.ids].sort()).toEqual([1, 2]);
    expect(bulkActionBody.action).toBe('delete');

    await expect(page.getByTestId('batch-action-bar')).not.toBeVisible({ timeout: 5000 });
  });

  test('deleting one selected proposal drops it from the bar and keeps the rest', {
    tag: ['@outcome:success', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    // The batch bar counted an id list nobody reconciled, so a deleted row
    // stayed in the count. Same defect the accounting bar had.
    const rows = mockProposals.map((p) => ({ ...p }));
    await mockApi(page, async ({ apiPath, route }) => {
      if (apiPath === 'auth/check/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };
      }
      if (apiPath === 'proposals/' && route.request().method() === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(rows) };
      }
      if (apiPath === 'proposals/dashboard/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify({ total: 3, by_status: {}, conversion_rate: 0, avg_close_days: 0 }) };
      }
      if (apiPath === 'proposals/alerts/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (/^proposals\/\d+\/delete\/$/.test(apiPath) && route.request().method() === 'DELETE') {
        const id = Number(apiPath.split('/')[1]);
        const index = rows.findIndex((row) => row.id === id);
        if (index !== -1) rows.splice(index, 1);
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return null;
    });
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('proposal-select-1').check();
    await page.getByTestId('proposal-select-3').check();
    const batchBar = page.getByTestId('batch-action-bar');
    await expect(batchBar).toContainText('2 seleccionados');

    // Same trigger the actions-modal spec uses: the row kebab carries no
    // label of its own. The bar has its own "Eliminar" too, so the modal item
    // is matched by its description instead.
    await page.getByTestId('proposal-actions-3').click();
    await page.getByRole('button', { name: /Elimina permanentemente/ }).click();
    await page.getByTestId('confirm-type-input').fill('DELETE');
    await page.getByTestId('confirm-modal-confirm').click();

    await expect(batchBar).toContainText('1 seleccionado');
  });

  test('select-all header checkbox selects all visible rows', {
    tag: ['@outcome:display', ...ADMIN_PROPOSAL_BATCH_ACTIONS, '@role:admin'],
  }, async ({ page }) => {
    await setupMock(page);
    await page.goto('/panel/proposals');
    await expect(page.getByText('Client A')).toBeVisible({ timeout: 10000 });

    // Click header checkbox (select all)
    await page.getByTestId('proposal-select-page').check();

    // Should show count matching total proposals
    await expect(page.getByText('3 seleccionados')).toBeVisible({ timeout: 5000 });
  });
});
