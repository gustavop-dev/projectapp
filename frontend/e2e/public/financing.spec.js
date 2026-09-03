import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'
import { financingProgramFixture } from '../helpers/financing-fixture.js'
import {
  PUBLIC_FINANCING_LANGUAGE,
  PUBLIC_FINANCING_LOAD,
  PUBLIC_FINANCING_OVERVIEW,
  PUBLIC_FINANCING_PDF,
  PUBLIC_FINANCING_SHARE,
  PUBLIC_FINANCING_TERMS,
} from '../helpers/flow-tags.js'


function json(status, body) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) }
}

async function setupApi(page, scenario = {}) {
  await mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'financing/public/pdf/' && method === 'GET') {
      const language = new URL(route.request().url()).searchParams.get('lang') || 'es'
      if (scenario.pdfUnavailable) return json(503, { detail: 'Unavailable' })
      scenario.pdfLanguage = language
      return {
        status: 200,
        contentType: 'application/pdf',
        headers: {
          'Content-Disposition': `attachment; filename="${language === 'en' ? 'software-financing-program.pdf' : 'programa-financiacion-software.pdf'}"`,
        },
        body: '%PDF-1.4 financing',
      }
    }
    if (apiPath === 'financing/public/' && method === 'GET') {
      if (scenario.programUnavailable) return json(503, { detail: 'Unavailable' })
      const language = new URL(route.request().url()).searchParams.get('lang') || 'es'
      return json(200, financingProgramFixture(language))
    }
    return null
  })
}

async function openFromFooter(page) {
  await page.goto('/es-co', { waitUntil: 'domcontentloaded' })
  const link = page.getByRole('link', { name: 'Módulo de financiación', exact: true }).first()
  await link.scrollIntoViewIfNeeded()
  await link.click()
  await expect(page).toHaveURL(/\/es-co\/financing$/)
  await expect(page.getByRole('heading', { name: 'Construimos hoy. Crecemos contigo.' })).toBeVisible()
}

test.describe('Public financing program', () => {
  test.setTimeout(60_000)

  test('shows the financing program after footer navigation', {
    tag: [...PUBLIC_FINANCING_OVERVIEW, '@role:guest', '@outcome:display', '@responsive:public'],
  }, async ({ page }) => {
    await setupApi(page)
    await openFromFooter(page)

    await expect(page.getByTestId('financing-option-five-year')).toContainText('Alianza a 5 años')
    await expect(page.getByTestId('financing-option-three-year')).toContainText('Alianza a 3 años')
    await expect(page.getByTestId('financing-condition-calculator')).toContainText('Calculadora de requerimientos')
    await expect(page.getByTestId('financing-condition-payment-discipline')).toContainText('aumenta en 1% el costo vigente del Hosting')
    await expect(page.getByTestId('financing-option-five-year')).toContainText('dos ciclos')
    await expect(page.getByTestId('financing-calculator-input-output')).toContainText('Qué se obtiene')
    await expect(page.getByTestId('financing-package-facts')).toContainText('No acumula horas')
    await expect(page.getByTestId('financing-whatsapp-cta')).toHaveAttribute('href', /wa\.me\/573238122373/)
    await expect(page.locator('nav[aria-label="Main navigation"]')).toHaveCount(0)
  })

  test('switches the financing program to English', {
    tag: [...PUBLIC_FINANCING_LANGUAGE, '@role:guest', '@outcome:success'],
  }, async ({ page }) => {
    await setupApi(page)
    await openFromFooter(page)

    await page.getByTestId('financing-language-en').click()

    await expect(page).toHaveURL(/\/en-us\/financing$/)
    await expect(page.getByRole('heading', { name: 'We build today. We grow with you.' })).toBeVisible()
    await expect(page.getByTestId('financing-option-five-year')).toContainText('5-year partnership')
  })

  test('expands the code custody rule', {
    tag: [...PUBLIC_FINANCING_TERMS, '@role:guest', '@outcome:success'],
  }, async ({ page }) => {
    await setupApi(page)
    await openFromFooter(page)
    const trigger = page.getByTestId('financing-term-trigger-code-custody')

    await trigger.click()

    await expect(trigger).toHaveAttribute('aria-expanded', 'true')
    await expect(page.getByTestId('financing-term-code-custody'))
      .toContainText('La custodia no transfiere la propiedad intelectual.')
  })

  test('copies the localized financing URL', {
    tag: [...PUBLIC_FINANCING_SHARE, '@role:guest', '@outcome:success'],
  }, async ({ page, context }) => {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'])
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'share', { configurable: true, value: undefined })
    })
    await setupApi(page)
    await openFromFooter(page)

    await page.getByTestId('financing-share').click()

    expect(await page.evaluate(() => navigator.clipboard.readText()))
      .toMatch(/\/es-co\/financing$/)
  })

  test('downloads the Spanish financing booklet', {
    tag: [...PUBLIC_FINANCING_PDF, '@role:guest', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openFromFooter(page)

    const downloadPromise = page.waitForEvent('download')
    await page.getByTestId('financing-download-pdf').click()
    const download = await downloadPromise

    expect(download.suggestedFilename()).toBe('programa-financiacion-software.pdf')
    expect(scenario.pdfLanguage).toBe('es')
  })

  test('shows a PDF failure without leaving the program', {
    tag: [...PUBLIC_FINANCING_PDF, '@role:guest', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { pdfUnavailable: true })
    await openFromFooter(page)

    await page.getByTestId('financing-download-pdf').click()

    await expect(page.getByRole('alert')).toContainText('No pudimos generar el PDF')
    await expect(page.getByRole('heading', { name: 'Construimos hoy. Crecemos contigo.' })).toBeVisible()
  })

  test('recovers after the program request fails', {
    tag: [...PUBLIC_FINANCING_LOAD, '@role:guest', '@outcome:failure', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = { programUnavailable: true }
    await setupApi(page, scenario)
    await page.goto('/es-co/financing', { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('heading', { name: 'No pudimos cargar el módulo de financiación.' })).toBeVisible()
    scenario.programUnavailable = false

    await page.getByRole('button', { name: 'Reintentar' }).click()

    await expect(page.getByRole('heading', { name: 'Construimos hoy. Crecemos contigo.' })).toBeVisible()
  })
})
