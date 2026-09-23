import { test, expect } from '../helpers/test.js'
import { mockCaptchaProvider, captchaCredentials } from '../helpers/captcha.js'
import { PLATFORM_LOGIN } from '../helpers/flow-tags.js'

test.describe('Platform CAPTCHA', () => {
  test.setTimeout(60_000)

  async function openLogin(page) {
    await page.goto('/es-co/platform/login', { waitUntil: 'domcontentloaded' })
    await page.getByLabel('Email', { exact: true }).fill(captchaCredentials.email)
    await page.getByLabel('Contraseña', { exact: true }).fill(captchaCredentials.password)
  }

  test('opens the client portal after a verified login', {
    tag: [...PLATFORM_LOGIN, '@outcome:success', '@role:platform-client'],
  }, async ({ page }, testInfo) => {
    await mockCaptchaProvider(page, testInfo.testId)
    await openLogin(page)
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeDisabled()

    await page.getByRole('checkbox', { name: 'No soy un robot (prueba)' }).check()
    await page.getByRole('button', { name: 'Iniciar sesión' }).click()

    await expect(page).toHaveURL(/\/platform\/documents$/)
    await expect(page.getByRole('heading', { name: 'Mis documentos', exact: true })).toBeVisible()
  })

  test('rejects an invalid token received from the widget', {
    tag: [...PLATFORM_LOGIN, '@outcome:error', '@role:guest'],
  }, async ({ page }, testInfo) => {
    await mockCaptchaProvider(page, testInfo.testId, { mode: 'invalid' })
    await openLogin(page)

    await page.getByRole('checkbox', { name: 'No soy un robot (prueba)' }).check()
    await page.getByRole('button', { name: 'Iniciar sesión' }).click()

    await expect(page.getByText('Verificación de captcha fallida. Intenta de nuevo.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeDisabled()
  })

  test('requires renewed verification after wrong credentials', {
    tag: [...PLATFORM_LOGIN, '@outcome:error', '@role:guest'],
  }, async ({ page }, testInfo) => {
    await mockCaptchaProvider(page, testInfo.testId)
    await openLogin(page)
    await page.getByLabel('Contraseña', { exact: true }).fill('wrong-password')

    await page.getByRole('checkbox', { name: 'No soy un robot (prueba)' }).check()
    await page.getByRole('button', { name: 'Iniciar sesión' }).click()

    await expect(page.getByText('Credenciales incorrectas.')).toBeVisible()
    await expect(page.getByRole('checkbox', { name: 'No soy un robot (prueba)' })).not.toBeChecked()
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeDisabled()
  })

  test('reports provider unavailability without opening a session', {
    tag: [...PLATFORM_LOGIN, '@outcome:failure', '@role:guest'],
  }, async ({ page }, testInfo) => {
    await mockCaptchaProvider(page, testInfo.testId, { mode: 'unavailable' })
    await openLogin(page)

    await page.getByRole('checkbox', { name: 'No soy un robot (prueba)' }).check()
    await page.getByRole('button', { name: 'Iniciar sesión' }).click()

    await expect(page.getByText('No pudimos verificar el captcha. Reintenta en unos momentos.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeDisabled()
    await expect(page).toHaveURL(/\/platform\/login$/)
  })

  test('recovers from a failed script load', {
    tag: [...PLATFORM_LOGIN, '@outcome:failure', '@role:guest'],
  }, async ({ page }, testInfo) => {
    await mockCaptchaProvider(page, testInfo.testId, { failScript: true })
    await openLogin(page)
    await expect(page.getByText('No pudimos cargar el captcha. Reintenta en unos momentos.')).toBeVisible()
    await page.unroute('https://www.google.com/recaptcha/api.js*')
    await mockCaptchaProvider(page, testInfo.testId)

    await page.getByRole('button', { name: 'Reintentar' }).click()
    await page.getByRole('checkbox', { name: 'No soy un robot (prueba)' }).check()

    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeEnabled()
  })
})
