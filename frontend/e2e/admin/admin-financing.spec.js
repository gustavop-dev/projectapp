import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'
import { setAuthLocalStorage } from '../helpers/auth.js'
import { financingProgramFixture } from '../helpers/financing-fixture.js'
import { financingSettingsFixture } from '../helpers/financing-agreement-fixture.js'
import { ADMIN_FINANCING_DISTRIBUTION, ADMIN_FINANCING_EXPLAINER } from '../helpers/flow-tags.js'
import { PANEL_BREAKPOINTS } from '../../config/responsive.js'


function json(status, body) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) }
}

async function setupApi(page, scenario = {}) {
  await mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return json(200, { user: { username: 'admin', is_staff: true } })
    if (apiPath === 'proposals/' && method === 'GET') return json(200, [])
    if (apiPath === 'proposals/dashboard/') return json(200, { total: 0, by_status: {} })
    if (apiPath === 'proposals/alerts/') return json(200, [])
    if (apiPath === 'financing/settings/' && method === 'GET') {
      return json(200, financingSettingsFixture())
    }
    if (apiPath === 'financing/agreements/' && method === 'GET') {
      return json(200, {
        count: 0,
        limit: 25,
        offset: 0,
        results: [],
        stats: { total_active_records: 0, archived: 0, by_status: {} },
      })
    }
    if (apiPath === 'financing/public/pdf/' && method === 'GET') {
      scenario.pdfLanguage = new URL(route.request().url()).searchParams.get('lang') || 'es'
      return {
        status: 200,
        contentType: 'application/pdf',
        headers: { 'Content-Disposition': 'attachment; filename="programa-financiacion-software.pdf"' },
        body: '%PDF-1.4 financing',
      }
    }
    if (apiPath === 'financing/public/' && method === 'GET') {
      if (scenario.programUnavailable) return json(503, { detail: 'Unavailable' })
      const language = new URL(route.request().url()).searchParams.get('lang') || 'es'
      return json(200, financingProgramFixture(language, {
        catalogSynced: scenario.catalogSynced,
      }))
    }
    return null
  })
}

async function openFinancing(page) {
  await page.goto('/es-co/panel/financing', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('financing-public-url')).toBeVisible({ timeout: 30_000 })
}

test.describe('Admin financing distribution', () => {
  test.setTimeout(60_000)

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, {
      token: 'e2e-admin',
      userAuth: { id: 1, role: 'admin', is_staff: true },
    })
  })

  test('navigates from Comercial to the financing preview', {
    tag: [...ADMIN_FINANCING_DISTRIBUTION, '@role:admin', '@outcome:display', '@responsive:commercial'],
  }, async ({ page }) => {
    await setupApi(page)
    // quality: allow-deep-link (the authenticated proposals list is the Comercial entry point; this test then reaches financing through the visible sidebar)
    await page.goto('/es-co/panel/proposals', { waitUntil: 'domcontentloaded' })
    if (page.viewportSize().width < PANEL_BREAKPOINTS.landscape) {
      await page.getByRole('button', { name: 'Abrir menú' }).click()
    }
    const link = page.getByRole('link', { name: 'Financiación', exact: true })

    await link.click()

    await expect(page).toHaveURL(/\/es-co\/panel\/financing$/)
    await expect(page.getByRole('heading', { name: 'Módulo de financiación' })).toBeVisible()
    await expect(page.getByTestId('financing-public-url'))
      .toHaveValue('https://projectapp.co/es-co/financing')
    await expect(page.getByTestId('financing-option-five-year')).toContainText('Alianza a 5 años')
  })

  test('copies the canonical public financing URL', {
    tag: [...ADMIN_FINANCING_DISTRIBUTION, '@role:admin', '@outcome:success'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    await setupApi(page)
    // quality: allow-deep-link (sidebar navigation is covered separately; this isolates clipboard distribution)
    await openFinancing(page)

    await page.getByTestId('financing-copy-public-url').click()

    expect(await page.evaluate(() => navigator.clipboard.readText()))
      .toBe('https://projectapp.co/es-co/financing')
    await expect(page.getByRole('alert')).toContainText('URL pública copiada')
  })

  test('downloads the public booklet from the distribution card', {
    tag: [...ADMIN_FINANCING_DISTRIBUTION, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    // quality: allow-deep-link (sidebar navigation is covered separately; this isolates the PDF shortcut)
    await openFinancing(page)
    await expect(page.getByTestId('financing-public-url'))
      .toHaveValue('https://projectapp.co/es-co/financing')

    const downloadPromise = page.waitForEvent('download')
    await page.getByTestId('financing-panel-download-pdf').click()
    const download = await downloadPromise

    expect(download.suggestedFilename()).toBe('programa-financiacion-software.pdf')
    expect(scenario.pdfLanguage).toBe('es')
  })

  test('keeps the package fallback visible after changing language', {
    tag: [...ADMIN_FINANCING_DISTRIBUTION, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupApi(page, { catalogSynced: false })
    // quality: allow-deep-link (sidebar navigation is covered separately; this isolates catalog fallback visibility)
    await openFinancing(page)

    await expect(page.getByTestId('financing-package-warning'))
      .toContainText('Paquete de horas en modo de respaldo')

    await page.getByTestId('financing-language-en').click()

    await expect(page).toHaveURL(/\/en-us\/panel\/financing$/)
    await expect(page.getByTestId('financing-package-warning'))
      .toContainText('Hour package fallback is active')
  })

  test('retries after the financing program request fails', {
    tag: [...ADMIN_FINANCING_DISTRIBUTION, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    // quality: allow-deep-link (isolates the panel's API failure and retry states)
    const scenario = { programUnavailable: true }
    await setupApi(page, scenario)
    await page.goto('/es-co/panel/financing', { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('alert')).toContainText('No pudimos cargar el módulo de financiación')
    scenario.programUnavailable = false

    await page.getByRole('button', { name: 'Reintentar' }).click()

    await expect(page.getByTestId('financing-public-url')).toBeVisible()
  })
  test('previews the financing explainer once from the Programa tab', {
    tag: [...ADMIN_FINANCING_EXPLAINER, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupApi(page)
    await openFinancing(page)
    await expect(page.getByTestId('financing-program')).toBeVisible()
    const card = page.getByTestId('financing-explainer-card')
    await expect(card).toContainText('Video explicativo del programa')
    await expect(page.getByTestId('financing-program').getByTestId('financing-explainer-card')).toHaveCount(0)

    await page.getByTestId('financing-explainer-play').click()

    await expect(page.getByTestId('financing-explainer-player')).toBeVisible()
  })
})
