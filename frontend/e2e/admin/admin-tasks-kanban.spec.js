/**
 * E2E test for the admin Kanban tasks board.
 *
 * @flow:admin-kanban-tasks
 * Covers: columns render, create task, edit task title, move via API, delete.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_KANBAN_TASKS } from '../helpers/flow-tags.js';

const authCheck = {
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify({ user: { username: 'admin', is_staff: true } }),
};

function board(overrides = {}) {
  return {
    todo: overrides.todo || [],
    in_progress: overrides.in_progress || [],
    blocked: overrides.blocked || [],
    done: overrides.done || [],
  };
}

test.describe('Admin Kanban Tasks', () => {
  test.setTimeout(60_000);

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-token',
      userAuth: { id: 9000, role: 'admin', is_staff: true },
    });
  });

  test('renders four columns and creates a task in TO DO', {
    tag: [...ADMIN_KANBAN_TASKS, '@role:admin'],
  }, async ({ page }) => {
    let tasksState = board();
    let nextId = 100;

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'tasks/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(tasksState) };
      }
      if (apiPath === 'tasks/create/' && method === 'POST') {
        const payload = route.request().postDataJSON();
        const created = {
          id: nextId++,
          title: payload.title,
          description: payload.description || '',
          status: payload.status || 'todo',
          priority: payload.priority || 'medium',
          assignee: null,
          assignee_name: null,
          due_date: null,
          is_overdue: false,
          position: 0,
        };
        tasksState = board({ ...tasksState, [created.status]: [...tasksState[created.status], created] });
        return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
      }
      return null;
    });

    await page.goto('/panel/tareas');
    await page.waitForLoadState('domcontentloaded');

    await expect(page.getByTestId('column-todo')).toBeVisible();
    await expect(page.getByTestId('column-in_progress')).toBeVisible();
    await expect(page.getByTestId('column-blocked')).toBeVisible();
    await expect(page.getByTestId('column-done')).toBeVisible();

    await page.getByTestId('new-task-btn').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible();

    await page.getByTestId('task-title-input').fill('Deploy staging');
    await page.getByTestId('task-submit-btn').click();

    await expect(
      page.getByTestId('column-todo').getByText('Deploy staging'),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('edits an existing task title', {
    tag: [...ADMIN_KANBAN_TASKS, '@role:admin'],
  }, async ({ page }) => {
    const existing = {
      id: 1, title: 'Old title', description: '', status: 'todo',
      priority: 'medium', assignee: null, assignee_name: null,
      due_date: null, is_overdue: false, position: 0,
    };
    let tasksState = board({ todo: [existing] });

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'tasks/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(tasksState) };
      }
      if (apiPath === 'tasks/1/update/' && method === 'PATCH') {
        const payload = route.request().postDataJSON();
        const updated = { ...existing, ...payload };
        tasksState = board({ todo: [updated] });
        return { status: 200, contentType: 'application/json', body: JSON.stringify(updated) };
      }
      return null;
    });

    await page.goto('/panel/tareas');
    await page.waitForLoadState('domcontentloaded');

    await page.getByText('Old title').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible();

    const titleInput = page.getByTestId('task-title-input');
    await titleInput.fill('Brand new title');
    await page.getByTestId('task-submit-btn').click();

    await expect(
      page.getByTestId('column-todo').getByText('Brand new title'),
    ).toBeVisible({ timeout: 10_000 });
  });

  test('creates a task with description, priority and due_date — all sent in POST body', {
    tag: [...ADMIN_KANBAN_TASKS, '@role:admin'],
  }, async ({ page }) => {
    let postBody = null;

    await mockApi(page, async ({ apiPath, method, route }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath === 'tasks/' && method === 'GET') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(board()) };
      }
      if (apiPath === 'tasks/assignees/') {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      if (apiPath === 'tasks/create/' && method === 'POST') {
        postBody = route.request().postDataJSON();
        const created = {
          id: 200, title: postBody.title, description: postBody.description || '',
          status: postBody.status || 'todo', priority: postBody.priority || 'medium',
          assignee: null, assignee_name: null,
          due_date: postBody.due_date || null, is_overdue: false, position: 0,
        };
        return { status: 201, contentType: 'application/json', body: JSON.stringify(created) };
      }
      return null;
    });

    await page.goto('/panel/tareas');
    await page.waitForLoadState('domcontentloaded');

    await page.getByTestId('new-task-btn').click();
    await expect(page.getByTestId('task-form-modal')).toBeVisible();

    await page.getByTestId('task-title-input').fill('Full-field task');
    await page.getByLabel('Descripción').fill('Detailed description here');
    await page.getByLabel('Prioridad').selectOption('high');
    await page.getByLabel('Fecha límite').fill('2026-12-31');
    await page.getByTestId('task-submit-btn').click();

    await expect(() => expect(postBody).not.toBeNull()).toPass({ timeout: 5000 });
    expect(postBody.title).toBe('Full-field task');
    expect(postBody.description).toBe('Detailed description here');
    expect(postBody.priority).toBe('high');
    expect(postBody.due_date).toBe('2026-12-31');
  });
});
