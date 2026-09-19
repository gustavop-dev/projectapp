import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'

import { ADMIN_PWA_INSTALL } from '../helpers/flow-tags.js'

async function openPanel(page) {
  await mockApi(page, async ({ apiPath }) => apiPath === 'auth/check/' ? {
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ user: { username: 'pwa-admin', is_staff: true } }),
  } : null)
  await page.goto('/es-co/panel/views', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible()
}

async function installEvent(page, outcome) {
  // Only the OS-owned dialog is simulated. The real component consumes the
  // event, drives its prompt, handles the result and updates the visible UI.
  await page.evaluate((result) => {
    const event = new Event('beforeinstallprompt', { cancelable: true })
    event.prompt = () => result === 'failed' ? Promise.reject(new Error('unavailable')) : Promise.resolve()
    event.userChoice = Promise.resolve({ outcome: result })
    window.dispatchEvent(event)
  }, outcome)
}

test.describe('Panel installation', () => {
  test.setTimeout(60_000)

  test('installs from the desktop navigation', {
    tag: [...ADMIN_PWA_INSTALL, '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    await openPanel(page)
    await installEvent(page, 'accepted')
    await page.getByTestId('panel-pwa-install').click()
    await expect(page.getByRole('heading', { name: 'Mapa de vistas', level: 1 })).toBeVisible()
    await expect(page.getByTestId('panel-pwa-install')).toHaveCount(0)
    await expect(page.getByTestId('panel-pwa-invitation')).toHaveCount(0)
  })

  test('opens installation help from the mobile menu', {
    tag: [...ADMIN_PWA_INSTALL, '@outcome:display', '@role:admin'],
  }, async ({ page }) => {
    // quality: allow-deep-link (the shared layout action is available on every panel page; the user reaches it by opening the mobile navigation)
    await page.setViewportSize({ width: 412, height: 915 })
    await openPanel(page)
    await page.getByRole('button', { name: 'Abrir menú' }).click()
    await page.getByRole('dialog', { name: 'Menú principal' }).getByTestId('panel-pwa-install').click()
    const dialog = page.getByRole('dialog', { name: 'Instalar ProjectApp' })
    await expect(dialog).toContainText('Chrome o Edge')
    await expect(dialog).toContainText('Necesitas conexión a internet')
    await page.getByRole('button', { name: 'Cerrar ayuda de instalación' }).click()
    await expect(dialog).toHaveCount(0)
  })

  test('keeps installation available after cancelling the native dialog', {
    tag: [...ADMIN_PWA_INSTALL, '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    await openPanel(page)
    await installEvent(page, 'dismissed')
    await page.getByTestId('panel-pwa-install').click()
    await expect(page.getByTestId('panel-pwa-install')).toBeEnabled()
    await page.getByTestId('panel-pwa-install').click()
    await expect(page.getByRole('dialog', { name: 'Instalar ProjectApp' })).toContainText('Chrome o Edge')
  })

  test('explains a failed native installation', {
    tag: [...ADMIN_PWA_INSTALL, '@outcome:failure', '@role:admin'],
  }, async ({ page }) => {
    await openPanel(page)
    await installEvent(page, 'failed')
    await page.getByTestId('panel-pwa-install').click()
    await expect(page.getByRole('alert')).toHaveText('No se pudo abrir la instalación. Puedes volver a intentarlo o usar el menú del navegador.')
  })

  test('remembers dismissal of the invitation during this session', {
    tag: [...ADMIN_PWA_INSTALL, '@outcome:success', '@role:admin'],
  }, async ({ page }) => {
    await openPanel(page)
    await page.getByRole('link', { name: 'Dashboard', exact: true }).click()
    await page.getByRole('button', { name: 'Cerrar invitación de instalación' }).click()
    await page.reload({ waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('panel-pwa-install')).toBeVisible()
    await expect(page.getByTestId('panel-pwa-invitation')).toHaveCount(0)
  })
})
