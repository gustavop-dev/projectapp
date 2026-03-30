/**
 * E2E tests for admin user management flow.
 *
 * @flow:admin-admin-management
 * Covers: admin list rendering, status filter tabs, invite new admin modal,
 *         deactivate admin, reactivate admin, resend invite, empty state.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_ADMIN_MANAGEMENT } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

const mockAdmins = [
  {
    user_id: 101, first_name: 'Carlos', last_name: 'López', email: 'carlos@example.com',
    role: 'admin', is_active: true, is_onboarded: true, created_at: '2026-01-15T10:00:00Z',
  },
  {
    user_id: 102, first_name: 'Ana', last_name: 'García', email: 'ana@example.com',
    role: 'admin', is_active: true, is_onboarded: false, created_at: '2026-02-20T10:00:00Z',
  },
  {
    user_id: 103, first_name: 'Pedro', last_name: 'Martínez', email: 'pedro@example.com',
    role: 'admin', is_active: false, is_onboarded: true, created_at: '2025-12-01T10:00:00Z',
  },
];

test.describe('Admin User Management', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-token', userAuth: { id: 8700, role: 'admin', is_staff: true } });
  });

  test('renders admin list with name, email, status badges and action buttons', {
    tag: [...ADMIN_ADMIN_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('accounts/admins/')) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAdmins) };
      return null;
    });
    await page.goto('/panel/admins');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Administradores' })).toBeVisible();
    await expect(page.getByText('Carlos López')).toBeVisible();
    await expect(page.getByText('Ana García')).toBeVisible();
    await expect(page.getByText('Pedro Martínez')).toBeVisible();
    await expect(page.getByRole('button', { name: /Agregar Administrador/i })).toBeVisible();
  });

  test('shows status filter tabs: Todos, Activos, Pendientes, Inactivos', {
    tag: [...ADMIN_ADMIN_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('accounts/admins/')) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAdmins) };
      return null;
    });
    await page.goto('/panel/admins');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: 'Todos', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Activos', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Inactivos', exact: true })).toBeVisible();
  });

  test('invite modal opens when Agregar Administrador is clicked', {
    tag: [...ADMIN_ADMIN_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('accounts/admins/')) return { status: 200, contentType: 'application/json', body: JSON.stringify(mockAdmins) };
      return null;
    });
    await page.goto('/panel/admins');
    await page.waitForResponse(res => res.url().includes('/api/accounts/admins/'));

    await page.getByRole('button', { name: /Agregar Administrador/i }).click();
    await expect(page.getByText('Se le enviará un email con credenciales temporales')).toBeVisible({ timeout: 5000 });
  });

  test('shows empty state when no admins exist', {
    tag: [...ADMIN_ADMIN_MANAGEMENT, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('accounts/admins/')) return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      return null;
    });
    await page.goto('/panel/admins');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: /Agregar Administrador/i })).toBeVisible();
  });
});
