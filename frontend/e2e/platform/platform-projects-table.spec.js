/**
 * E2E tests for the platform projects table (post IA refactor).
 *
 * @flow:platform-project-list
 * Covers: table renders rows, chevron click drills into project detail.
 */
import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'
import { PLATFORM_PROJECT_LIST } from '../helpers/flow-tags.js'

const ADMIN_USER = {
  user_id: 1, email: 'admin@example.com', role: 'admin',
  first_name: 'Admin', last_name: 'User',
  is_onboarded: true, profile_completed: true,
}

const ROWS = [
  {
    id: 1, name: 'Project A', status: 'active', progress: 50,
    client_name: 'Ada Lovelace', client_email: 'ada@e.co', client_id: 9,
    bugs_open_count: 2, changes_pending_count: 1,
    next_deliverable: null, last_activity_at: new Date().toISOString(),
  },
]

test.describe('Platform projects table', () => {
  test.setTimeout(60_000)

  test(
    'table renders rows and chevron drills into detail',
    { tag: PLATFORM_PROJECT_LIST },
    async ({ page }) => {
      await mockApi(page, async ({ apiPath, method }) => {
        if (method === 'GET' && apiPath === 'accounts/me/') {
          return { status: 200, contentType: 'application/json', body: JSON.stringify(ADMIN_USER) }
        }
        if (method === 'GET' && apiPath === 'accounts/projects/') {
          return { status: 200, contentType: 'application/json', body: JSON.stringify(ROWS) }
        }
        if (method === 'GET' && apiPath === 'accounts/projects/1/') {
          return { status: 200, contentType: 'application/json', body: JSON.stringify({ ...ROWS[0] }) }
        }
        if (method === 'GET' && apiPath === 'accounts/projects/1/phases/') {
          return { status: 200, contentType: 'application/json', body: JSON.stringify([]) }
        }
        return null
      })

      // Pre-seed an authenticated session via localStorage hooks before navigation.
      await page.addInitScript((user) => {
        localStorage.setItem('platform_access_token', 'mock-access')
        localStorage.setItem('platform_refresh_token', 'mock-refresh')
        localStorage.setItem('platform_user', JSON.stringify(user))
      }, ADMIN_USER)

      await page.goto('/es-co/platform/projects', { waitUntil: 'domcontentloaded' })

      await expect(page.locator('[data-testid="project-row-1"]')).toBeVisible({ timeout: 15000 })
      await expect(page.getByText('Ada Lovelace')).toBeVisible()

      await page.locator('[data-testid="project-row-1"]').click()
      await page.waitForURL(/\/platform\/projects\/1/, { waitUntil: 'domcontentloaded' })
    },
  )
})
