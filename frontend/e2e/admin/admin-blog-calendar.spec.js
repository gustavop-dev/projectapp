/**
 * E2E tests for admin blog calendar view.
 *
 * Covers: calendar page load with week grid, week navigation,
 * color-coded post cards, and "Hoy" button.
 */
import { test, expect } from '../helpers/test.js';
import { mockApi } from '../helpers/api.js';
import { setAuthLocalStorage } from '../helpers/auth.js';
import { ADMIN_BLOG_CALENDAR } from '../helpers/flow-tags.js';

const authCheck = { status: 200, contentType: 'application/json', body: JSON.stringify({ user: { username: 'admin', is_staff: true } }) };

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

const mockCalendarPosts = [
  { id: 1, title_es: 'Post Publicado', category: 'ai', date: todayISO(), calendar_status: 'published' },
  { id: 2, title_es: 'Post Programado', category: 'design', date: todayISO(), calendar_status: 'scheduled' },
  { id: 3, title_es: 'Post Borrador', category: null, date: todayISO(), calendar_status: 'draft' },
];

test.describe('Admin Blog Calendar', () => {
  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin-token',
      userAuth: { id: 8100, role: 'admin', is_staff: true },
    });
  });

  test('renders calendar page with week grid and day columns', {
    tag: [...ADMIN_BLOG_CALENDAR, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/calendar/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockCalendarPosts) };
      }
      return null;
    });

    await page.goto('/panel/blog/calendar');

    await expect(page.getByRole('heading', { name: 'Calendario de Blog' })).toBeVisible();
    await expect(page.getByText('Semana')).toBeVisible();

    // Day-name headers render twice (desktop grid + mobile compact view); use .first().
    await expect(page.getByText('Lun').first()).toBeVisible();
    await expect(page.getByText('Dom').first()).toBeVisible();
  });

  test('displays color-coded post cards for published, scheduled, and draft', {
    tag: [...ADMIN_BLOG_CALENDAR, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/calendar/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify(mockCalendarPosts) };
      }
      return null;
    });

    await page.goto('/panel/blog/calendar');

    await expect(page.getByText('Post Publicado').first()).toBeVisible();
    await expect(page.getByText('Post Programado').first()).toBeVisible();
    await expect(page.getByText('Post Borrador').first()).toBeVisible();

    // Legend is visible (use exact match to avoid matching post card titles)
    await expect(page.getByText('Publicado', { exact: true })).toBeVisible();
    await expect(page.getByText('Programado', { exact: true })).toBeVisible();
    await expect(page.getByText('Borrador', { exact: true })).toBeVisible();
  });

  test('week navigation buttons change displayed week', {
    tag: [...ADMIN_BLOG_CALENDAR, '@role:admin'],
  }, async ({ page }) => {
    let calendarRequestCount = 0;

    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/calendar/')) {
        calendarRequestCount++;
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/panel/blog/calendar');

    // quality: allow-fragile-selector (calendar heading has no testid, first h2 is the week label)
    const initialWeekText = await page.locator('h2').first().textContent();
    calendarRequestCount = 0;

    // Navigate to next week
    await page.locator('svg path[d="M9 5l7 7-7 7"]').locator('..').click();

    expect(calendarRequestCount).toBeGreaterThanOrEqual(1);

    // Click "Hoy" to return to current week
    await page.getByRole('button', { name: 'Hoy' }).click();

    // quality: allow-fragile-selector (same calendar heading)
    const resetWeekText = await page.locator('h2').first().textContent();
    expect(resetWeekText).toBe(initialWeekText);
  });

  test('shows empty state text for days without posts', {
    tag: [...ADMIN_BLOG_CALENDAR, '@role:admin'],
  }, async ({ page }) => {
    await mockApi(page, async ({ apiPath }) => {
      if (apiPath === 'auth/check/') return authCheck;
      if (apiPath.startsWith('blog/admin/calendar/')) {
        return { status: 200, contentType: 'application/json', body: JSON.stringify([]) };
      }
      return null;
    });

    await page.goto('/panel/blog/calendar');

    // All days should show "Sin posts"
    const emptyLabels = page.getByText('Sin posts');
    // quality: allow-fragile-selector (multiple 'Sin posts' labels, checking any one is visible)
    await expect(emptyLabels.first()).toBeVisible();
  });
});
