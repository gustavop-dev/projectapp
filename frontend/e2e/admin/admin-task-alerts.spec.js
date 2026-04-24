/**
 * E2E tests for admin Task Alerts — manual date-based alert management
 * inside the TaskFormModal (edit mode).
 *
 * Covers: Alertas section visibility, adding an alert, "Pendiente" badge,
 * and deleting an alert.
 *
 * @flow:admin-task-alert-management
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_TASK_ALERT_MANAGEMENT } from '../helpers/flow-tags.js';

const TASK_ID = 42;

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

const existingTask = {
  id: TASK_ID,
  title: 'Revisar propuesta cliente',
  description: '',
  status: 'in_progress',
  priority: 'high',
  assignee: null,
  assignee_name: null,
  due_date: '2026-05-01',
  is_overdue: false,
  position: 0,
};

function board(task = existingTask) {
  return { todo: [], in_progress: [task], blocked: [], done: [] };
}

function baseHandler(alertsState, extra = {}) {
  return async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return authCheck;
    if (apiPath === 'tasks/' && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(board()) };
    }
    if (apiPath === 'tasks/assignees/') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
    }
    if (apiPath === `tasks/${TASK_ID}/alerts/` && method === 'GET') {
      return { status: 200, contentType: 'application/json', body: JSON.stringify(alertsState) };
    }
    for (const [path, response] of Object.entries(extra)) {
      if (apiPath === path && (!response.method || response.method === method)) {
        return response;
      }
    }
    return null;
  };
}

test.describe('Admin Task — Alertas section', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 9000, role: 'admin', is_staff: true },
    });
  });

  test('Alertas section is visible when editing a task', {
    tag: [...ADMIN_TASK_ALERT_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, baseHandler([]));

    await page.goto('/panel/tasks');
    await page.waitForLoadState('domcontentloaded');

    await page.getByText('Revisar propuesta cliente').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible({ timeout: 10_000 });

    const modal = page.getByTestId('task-form-modal');
    await expect(modal.getByText('No hay alertas definidas.')).toBeVisible({ timeout: 10_000 });
    await expect(modal.getByRole('button', { name: '+ Agregar' }).first()).toBeVisible();
  });

  test('adding an alert calls POST and alert appears with Pendiente badge', {
    tag: [...ADMIN_TASK_ALERT_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    let alertsState = [];
    let nextAlertId = 1;
    let postCalled = false;

    await mockApi(page, async ({ apiPath, method, route }) => {
      const base = await baseHandler(alertsState)({ apiPath, method, route });
      if (base) return base;

      if (apiPath === `tasks/${TASK_ID}/alerts/create/` && method === 'POST') {
        postCalled = true;
        const payload = route.request().postDataJSON();
        const created = {
          id: nextAlertId++,
          notify_at: payload.notify_at,
          note: payload.note || '',
          sent: false,
          created_at: '2026-04-16T08:00:00Z',
        };
        alertsState = [...alertsState, created];
        return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
      }
      return null;
    });

    await page.goto('/panel/tasks');
    await page.waitForLoadState('domcontentloaded');

    await page.getByText('Revisar propuesta cliente').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible({ timeout: 10_000 });

    await page.locator('input[type="date"]').last().fill('2026-06-01');
    await page.locator('input[placeholder*="Revisar avance"]').fill('Llamar al cliente');
    await page.getByRole('button', { name: '+ Agregar' }).first().click();

    await expect(() => expect(postCalled).toBe(true)).toPass({ timeout: 5_000 });
    await expect(page.getByText('Pendiente')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('Llamar al cliente')).toBeVisible();
  });

  test('deleting an alert calls DELETE and removes it from the list', {
    tag: [...ADMIN_TASK_ALERT_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    const alert = {
      id: 77,
      notify_at: '2026-07-15',
      note: 'Revisar entregable',
      sent: false,
      created_at: '2026-04-16T08:00:00Z',
    };
    let alertsState = [alert];
    let deleteCalled = false;

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'tasks/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(board()) };
      }
      if (apiPath === 'tasks/assignees/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === `tasks/${TASK_ID}/alerts/` && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(alertsState) };
      }
      if (apiPath === `tasks/${TASK_ID}/alerts/77/delete/` && method === 'DELETE') {
        deleteCalled = true;
        alertsState = [];
        return { status: 204, contentType: 'application/json', body: '' };
      }
      return null;
    });

    await page.goto('/panel/tasks');
    await page.waitForLoadState('domcontentloaded');

    await page.getByText('Revisar propuesta cliente').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible({ timeout: 10_000 });

    await expect(page.getByText('Revisar entregable')).toBeVisible({ timeout: 10_000 });

    await page.locator('li').filter({ hasText: 'Revisar entregable' }).getByRole('button').click();

    await expect(() => expect(deleteCalled).toBe(true)).toPass({ timeout: 5_000 });
    await expect(page.getByText('No hay alertas definidas.')).toBeVisible({ timeout: 10_000 });
  });

  test('sent alert shows Enviada badge', {
    tag: [...ADMIN_TASK_ALERT_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    const sentAlert = {
      id: 88,
      notify_at: '2026-03-01',
      note: 'Notificación enviada',
      sent: true,
      created_at: '2026-03-01T08:00:00Z',
    };

    await mockApi(page, baseHandler([sentAlert]));

    await page.goto('/panel/tasks');
    await page.waitForLoadState('domcontentloaded');

    await page.getByText('Revisar propuesta cliente').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible({ timeout: 10_000 });

    const modal = page.getByTestId('task-form-modal');
    await expect(modal.locator('span', { hasText: /^Enviada$/ }).first()).toBeVisible({ timeout: 10_000 });
    await expect(modal.getByText('Notificación enviada')).toBeVisible();
  });
});
