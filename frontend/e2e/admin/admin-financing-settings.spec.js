import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'
import { setAuthLocalStorage } from '../helpers/auth.js'
import { financingSettingsFixture } from '../helpers/financing-agreement-fixture.js'
import { financingProgramFixture } from '../helpers/financing-fixture.js'
import { ADMIN_FINANCING_SETTINGS } from '../helpers/flow-tags.js'


function json(status, body) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) }
}

function emptyAgreementEnvelope() {
  return {
    count: 0,
    limit: 25,
    offset: 0,
    results: [],
    stats: { total_active_records: 0, archived: 0, by_status: {} },
  }
}

async function setupApi(page, scenario = {}) {
  scenario.settings ??= financingSettingsFixture()
  scenario.publishCount = 0

  await mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return json(200, { user: { username: 'admin', is_staff: true } })
    if (apiPath === 'proposals/' && method === 'GET') return json(200, [])
    if (apiPath === 'proposals/dashboard/') return json(200, { total: 0, by_status: {} })
    if (apiPath === 'proposals/alerts/') return json(200, [])
    if (apiPath === 'financing/public/' && method === 'GET') {
      return json(200, financingProgramFixture('es'))
    }
    if (apiPath === 'financing/agreements/' && method === 'GET') {
      return json(200, emptyAgreementEnvelope())
    }
    if (apiPath === 'financing/settings/' && method === 'GET') {
      if (scenario.settingsUnavailable) {
        return json(503, { detail: 'Servicio de políticas no disponible.' })
      }
      return json(200, scenario.settings)
    }
    if (apiPath === 'financing/settings/' && method === 'POST') {
      scenario.publishCount += 1
      scenario.publishedPayload = route.request().postDataJSON()
      const current = {
        ...scenario.settings.current,
        ...scenario.publishedPayload,
        id: 3,
        version: 3,
        minimum_initial_payment_percent: String(
          100 - Number(scenario.publishedPayload.maximum_financed_percent),
        ),
        created_by: 1,
        created_by_name: 'Admin Prueba',
        created_at: '2026-09-03T12:00:00Z',
      }
      scenario.settings = {
        ...scenario.settings,
        current,
        history: [current, ...scenario.settings.history],
      }
      return json(201, scenario.settings)
    }
    return null
  })
}

async function openSettings(page) {
  await page.goto('/es-co/panel/proposals', { waitUntil: 'domcontentloaded' })
  await page.getByRole('link', { name: 'Financiación', exact: true }).click()
  await page.getByTestId('financing-tab-settings').click()
  await expect(page).toHaveURL(/\/es-co\/panel\/financing\?tab=settings$/)
}

test.describe('Admin financing policy settings', () => {
  test.setTimeout(60_000)

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin',
      userAuth: { id: 1, role: 'admin', is_staff: true },
    })
  })

  test('shows the current financing policy revision', {
    tag: [...ADMIN_FINANCING_SETTINGS, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-deep-link (authenticated panel setup starts at the Comercial surface; the test reaches financing settings through the visible Financiación link and settings tab)
    await setupApi(page)
    await openSettings(page)

    await expect(page.getByTestId('financing-settings-minimum')).toHaveValue('20000000.00')
    await expect(page.getByTestId('financing-settings-maximum')).toHaveValue('140000000.00')
    await expect(page.getByTestId('financing-settings-minimum-initial')).toHaveValue('20.00%')
    await expect(page.getByText('Revisión vigente v2')).toBeVisible()
  })

  test('publishes a new financing policy revision', {
    tag: [...ADMIN_FINANCING_SETTINGS, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openSettings(page)
    await page.getByTestId('financing-settings-months').fill('18')

    await page.getByTestId('financing-settings-publish').click()
    await expect(page.getByTestId('confirm-modal-confirm')).toBeVisible()
    await page.getByTestId('confirm-modal-confirm').click()

    await expect(page.getByText('Revisión vigente v3')).toBeVisible()
    await expect(page.getByTestId('financing-settings-months')).toHaveValue('18')
    expect(scenario.publishedPayload.financing_months).toBe('18')
  })

  test('blocks a maximum below the configured minimum', {
    tag: [...ADMIN_FINANCING_SETTINGS, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openSettings(page)
    await page.getByTestId('financing-settings-maximum').fill('10000000')

    await page.getByTestId('financing-settings-publish').click()

    await expect(page.getByText('El monto máximo debe superar al mínimo.')).toBeVisible()
    expect(scenario.publishCount).toBe(0)
  })

  test('recovers after the policy request is unavailable', {
    tag: [...ADMIN_FINANCING_SETTINGS, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    const scenario = { settingsUnavailable: true }
    await setupApi(page, scenario)
    await openSettings(page)
    await expect(page.getByRole('alert')).toContainText('No fue posible cargar la política')
    scenario.settingsUnavailable = false

    await page.getByRole('button', { name: 'Reintentar' }).click()

    await expect(page.getByTestId('financing-settings-panel')).toBeVisible()
    await expect(page.getByText('Revisión vigente v2')).toBeVisible()
  })
})
