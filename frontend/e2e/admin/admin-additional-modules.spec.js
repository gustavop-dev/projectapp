import { test, expect } from '../helpers/test.js'
import { mockApi } from '../helpers/api.js'
import { setAuthLocalStorage } from '../helpers/auth.js'
import {
  ADMIN_ADDITIONAL_MODULES_CATALOG,
  ADMIN_ADDITIONAL_MODULES_MANAGE,
  ADMIN_ADDITIONAL_MODULES_PDF,
  ADMIN_ADDITIONAL_MODULES_REORDER,
  ADMIN_ADDITIONAL_MODULES_SHARE,
} from '../helpers/flow-tags.js'

const categories = [
  { id: 1, slug: 'commerce', name_es: 'Comercio', name_en: 'Commerce', order: 0, is_active: true, module_count: 2, active_module_count: 2 },
  { id: 2, slug: 'marketing', name_es: 'Marketing', name_en: 'Marketing', order: 1, is_active: true, module_count: 1, active_module_count: 1 },
]

function moduleItem(id, category, slug, name) {
  return {
    id, category, slug, icon: '＋', order: id, is_active: true,
    name_es: name, name_en: `${name} EN`,
    summary_es: `Resumen ${name}`, summary_en: `Summary ${name}`,
    what_is_es: 'Una capacidad integrada.', what_is_en: 'An integrated capability.',
    purpose_es: 'Automatizar el proceso.', purpose_en: 'Automate the process.',
    problems_solved_es: ['Trabajo manual'], problems_solved_en: ['Manual work'],
    integrations_es: ['API externa'], integrations_en: ['External API'],
    implementation_requirements_es: ['Credenciales'], implementation_requirements_en: ['Credentials'],
  }
}

const modules = [
  moduleItem(10, 1, 'electronic-invoicing', 'Facturación electrónica'),
  moduleItem(11, 1, 'regional-payments', 'Pagos regionales'),
  moduleItem(12, 2, 'landing-page', 'Landing page'),
]
const catalog = { revision: 'revision-1', categories, modules }
const trackedLink = {
  id: 1, uuid: '11111111-1111-4111-8111-111111111111',
  recipient_label: 'Acme — pagos', client: null, client_name: '', language: 'es',
  selected_modules: modules.slice(0, 2),
  public_path: '/es-co/additional-modules/share/11111111-1111-4111-8111-111111111111',
  is_active: true, revoked_at: null, view_count: 2,
  first_viewed_at: '2026-08-20T10:00:00Z', last_viewed_at: '2026-08-21T10:00:00Z',
  created_at: '2026-08-19T10:00:00Z',
}

function json(status, body) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) }
}

async function setupApi(page, scenario = {}) {
  let catalogCalls = 0
  await mockApi(page, async ({ apiPath, method, route }) => {
    if (apiPath === 'auth/check/') return json(200, { user: { username: 'admin', is_staff: true } })
    if (apiPath === 'proposals/' && method === 'GET') return json(200, [])
    if (apiPath === 'proposals/dashboard/') return json(200, { total: 0, by_status: {} })
    if (apiPath === 'proposals/alerts/') return json(200, [])
    if (apiPath === 'proposals/client-profiles/') return json(200, [])
    if (apiPath === 'additional-modules/admin/' && method === 'GET') {
      catalogCalls += 1
      if (scenario.catalogUnavailable || catalogCalls <= (scenario.catalogFailures || 0)) {
        return json(503, { detail: 'Servicio no disponible' })
      }
      return json(200, catalog)
    }
    if (apiPath === 'additional-modules/admin/shares/' && method === 'GET') return json(200, scenario.shareLinks || [])
    if (apiPath === 'additional-modules/admin/modules/' && method === 'POST') {
      scenario.modulePayload = route.request().postDataJSON()
      return scenario.moduleFailure ? json(500, { detail: 'No se pudo guardar el módulo.' }) : json(201, modules[0])
    }
    if (apiPath === 'additional-modules/admin/modules/10/' && method === 'PATCH') {
      scenario.updatePayload = route.request().postDataJSON()
      return scenario.moduleFailure ? json(500, { detail: 'No se pudo guardar el módulo.' }) : json(200, modules[0])
    }
    if (apiPath === 'additional-modules/admin/reorder/' && method === 'POST') {
      scenario.orderPayload = route.request().postDataJSON()
      return scenario.staleOrder
        ? json(409, { detail: 'El catálogo cambió.', code: 'stale_catalog_revision' })
        : json(200, { revision: 'revision-2' })
    }
    if (apiPath === 'additional-modules/admin/shares/' && method === 'POST') {
      scenario.sharePayload = route.request().postDataJSON()
      return scenario.shareFailure
        ? json(500, { detail: 'No se pudo generar el enlace.' })
        : json(201, trackedLink)
    }
    if (apiPath.endsWith('/revoke/') && method === 'POST') return json(200, { ...trackedLink, is_active: false })
    if (apiPath === 'additional-modules/admin/pdf/' && method === 'POST') {
      if (scenario.pdfFailure) return json(500, { detail: 'No se pudo generar el PDF.' })
      return { status: 200, contentType: 'application/pdf', headers: { 'Content-Disposition': 'attachment; filename="catalogo.pdf"' }, body: '%PDF-1.4 demo' }
    }
    return null
  })
}

async function openCatalog(page) {
  await page.goto('/es-co/panel/additional-modules', { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('additional-admin-module-10')).toBeVisible({ timeout: 30_000 })
}

async function openSelection(page, mode = 'share') {
  await page.getByRole('button', { name: mode === 'share' ? 'Generar enlace' : 'Descargar PDF' }).click()
  await expect(page.getByRole('heading', { name: mode === 'share' ? 'Preparar enlace compartible' : 'Preparar PDF' })).toBeVisible()
}

async function fillCreateForm(page) {
  await page.getByTestId('additional-module-new').click()
  const form = page.getByTestId('additional-module-form')
  await form.getByTestId('additional-module-category').selectOption('1')
  await form.getByTestId('additional-module-slug').fill('customer-portal')
  for (const [id, value] of Object.entries({
    'additional-module-name-es': 'Portal de clientes', 'additional-module-summary-es': 'Centraliza las solicitudes.',
    'additional-module-what-es': 'Un portal seguro.', 'additional-module-purpose-es': 'Dar autoservicio.',
    'additional-module-problems-es': 'Solicitudes dispersas', 'additional-module-integrations-es': 'CRM',
    'additional-module-requirements-es': 'Accesos del cliente',
  })) await form.locator(`#${id}`).fill(value)
  await form.getByRole('tab', { name: 'English' }).click()
  for (const [id, value] of Object.entries({
    'additional-module-name-en': 'Customer portal', 'additional-module-summary-en': 'Centralizes requests.',
    'additional-module-what-en': 'A secure portal.', 'additional-module-purpose-en': 'Enable self-service.',
    'additional-module-problems-en': 'Scattered requests', 'additional-module-integrations-en': 'CRM',
    'additional-module-requirements-en': 'Customer access',
  })) await form.locator(`#${id}`).fill(value)
  return form
}

test.describe('Additional modules admin catalog', () => {
  test.setTimeout(60_000)

  test.beforeEach(async ({ page }) => {
    await setAuthLocalStorage(page, { token: 'e2e-admin', userAuth: { id: 1, role: 'admin', is_staff: true } })
  })

  test('navigates from Comercial and displays grouped catalog data', {
    tag: [...ADMIN_ADDITIONAL_MODULES_CATALOG, '@role:admin', '@outcome:display', '@responsive:commercial'],
  }, async ({ page }) => {
    await setupApi(page)
    // quality: allow-deep-link (the authenticated proposals page is setup; this test exercises the Comercial sidebar navigation to the catalog)
    await page.goto('/es-co/panel/proposals', { waitUntil: 'domcontentloaded' })
    await page.getByRole('link', { name: 'Módulos adicionales' }).click()
    await expect(page.getByRole('heading', { name: 'Catálogo de módulos adicionales' })).toBeVisible()
    await expect(page.getByTestId('additional-admin-module-10')).toContainText('Facturación electrónica')
    await expect(page.getByTestId('additional-admin-module-12')).toContainText('Landing page')

    const detailOpener = page.getByTestId('additional-admin-module-10').getByRole('button', { name: 'Ver detalle' })
    await detailOpener.click()
    const detail = page.getByRole('dialog')
    await expect(detail.getByRole('heading', { name: 'Facturación electrónica' })).toHaveText('Facturación electrónica')
    for (const section of ['Qué es', 'Para qué sirve', 'Qué resuelve', 'Qué se integra', 'Qué hace falta para implementarlo']) {
      await expect(detail.getByRole('heading', { name: section })).toHaveCount(1)
    }
    await detail.getByRole('button', { name: 'Cerrar' }).click()
    await expect(detail).not.toBeVisible()
    await expect(detailOpener).toBeFocused()
  })

  test('retries after the catalog request fails', {
    tag: [...ADMIN_ADDITIONAL_MODULES_CATALOG, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { catalogFailures: 1 })
    const initialFailure = page.waitForResponse((response) => (
      response.url().endsWith('/api/additional-modules/admin/') && response.status() === 503
    ))
    await page.goto('/es-co/panel/additional-modules', { waitUntil: 'domcontentloaded' })
    await initialFailure
    await expect(page.getByRole('alert')).toContainText('No pudimos cargar el catálogo')
    await page.getByRole('button', { name: 'Reintentar' }).click()
    await expect(page.getByTestId('additional-admin-module-10')).toBeVisible()
  })

  test('validates incomplete bilingual module content', {
    tag: [...ADMIN_ADDITIONAL_MODULES_MANAGE, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await setupApi(page)
    await openCatalog(page)
    await page.getByTestId('additional-module-new').click()
    await page.getByTestId('additional-module-save').click()
    await expect(page.getByTestId('additional-module-form')).toContainText('Completa los campos obligatorios')
  })

  test('creates a complete bilingual module', {
    tag: [...ADMIN_ADDITIONAL_MODULES_MANAGE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openCatalog(page)
    const form = await fillCreateForm(page)
    await form.getByTestId('additional-module-save').click()
    await expect(form).not.toBeVisible()
    expect(scenario.modulePayload.name_es).toBe('Portal de clientes')
    expect(scenario.modulePayload.name_en).toBe('Customer portal')
    expect(scenario.modulePayload.problems_solved_es).toEqual(['Solicitudes dispersas'])
  })

  test('keeps the edit form open when the server rejects the save', {
    tag: [...ADMIN_ADDITIONAL_MODULES_MANAGE, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { moduleFailure: true })
    await openCatalog(page)
    await page.getByTestId('additional-admin-module-10').getByRole('button', { name: 'Editar' }).click()
    await page.getByTestId('additional-module-save').click()
    await expect(page.getByTestId('additional-module-form')).toContainText('No se pudo guardar el módulo')
  })

  test('persists bilingual module edits with PATCH and closes the form', {
    tag: [...ADMIN_ADDITIONAL_MODULES_MANAGE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openCatalog(page)
    await page.getByTestId('additional-admin-module-10').getByRole('button', { name: 'Editar' }).click()
    const form = page.getByTestId('additional-module-form')
    await form.locator('#additional-module-name-es').fill('Facturación electrónica automatizada')
    await form.getByTestId('additional-module-save').click()
    await expect(form).not.toBeVisible()
    expect(scenario.updatePayload.name_es).toBe('Facturación electrónica automatizada')
    expect(scenario.updatePayload.name_en).toBe('Facturación electrónica EN')
  })

  test('saves the new module order', {
    tag: [...ADMIN_ADDITIONAL_MODULES_REORDER, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openCatalog(page)
    await page.getByRole('button', { name: 'Reordenar' }).click()
    await page.getByRole('button', { name: 'Bajar: Facturación electrónica' }).click()
    await page.getByTestId('additional-catalog-order-save').click()
    await expect(page.getByRole('heading', { name: 'Orden del catálogo' })).not.toBeVisible()
    expect(scenario.orderPayload.module_groups[0].module_ids).toEqual([11, 10])
  })

  test('shows the recoverable stale-order message', {
    tag: [...ADMIN_ADDITIONAL_MODULES_REORDER, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { staleOrder: true })
    await openCatalog(page)
    await page.getByRole('button', { name: 'Reordenar' }).click()
    await page.getByTestId('additional-catalog-order-save').click()
    await expect(page.getByText('El catálogo cambió en otra sesión. Se recargó el orden más reciente.')).toBeVisible()
  })

  test('requires a selected module before creating a link', {
    tag: [...ADMIN_ADDITIONAL_MODULES_SHARE, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    await setupApi(page)
    await openCatalog(page)
    await openSelection(page)
    await page.getByTestId('additional-selection-submit').click()
    await expect(page.getByText('Selecciona al menos un módulo.')).toBeVisible()
  })

  test('generates a fixed-selection public link', {
    tag: [...ADMIN_ADDITIONAL_MODULES_SHARE, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    const scenario = {}
    await setupApi(page, scenario)
    await openCatalog(page)
    await openSelection(page)
    await page.getByTestId('additional-select-module-10').click()
    await page.getByTestId('additional-share-recipient').fill('Acme — pagos')
    await page.getByTestId('additional-selection-submit').click()
    await expect(page.getByText('Enlace listo para compartir')).toBeVisible()
    expect(scenario.sharePayload.selected_module_ids).toEqual([10])
    expect(scenario.sharePayload.recipient_label).toBe('Acme — pagos')
  })

  test('shows link-generation server failures inside the selection modal', {
    tag: [...ADMIN_ADDITIONAL_MODULES_SHARE, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { shareFailure: true })
    await openCatalog(page)
    await openSelection(page)
    await page.getByTestId('additional-select-module-10').click()
    await page.getByTestId('additional-share-recipient').fill('Acme')
    await page.getByTestId('additional-selection-submit').click()
    await expect(page.getByText('No se pudo generar el enlace.')).toBeVisible()
  })

  test('displays tracked openings and revokes a shared link', {
    tag: [...ADMIN_ADDITIONAL_MODULES_SHARE, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    await setupApi(page, { shareLinks: [trackedLink] })
    // quality: allow-deep-link (the commercial catalog navigation is covered above; this isolates the Seguimiento display and revoke behavior)
    await openCatalog(page)
    await page.getByRole('button', { name: 'Seguimiento' }).click()
    const history = page.getByTestId('additional-share-history')
    await expect(history).toContainText('Acme — pagos')
    await expect(history).toContainText('2 aperturas')
    await history.getByRole('button', { name: 'Revocar' }).click()
    await expect(history).toContainText('Retirado')
  })

  test('downloads the selected PDF', {
    tag: [...ADMIN_ADDITIONAL_MODULES_PDF, '@role:admin', '@outcome:success'],
  }, async ({ page }) => {
    await setupApi(page)
    await openCatalog(page)
    await openSelection(page, 'pdf')
    const downloadPromise = page.waitForEvent('download')
    await page.getByTestId('additional-selection-submit').click()
    const download = await downloadPromise
    expect(download.suggestedFilename()).toBe('catalogo-modulos-adicionales.pdf')
  })

  test('shows PDF generation failures without closing the selection', {
    tag: [...ADMIN_ADDITIONAL_MODULES_PDF, '@role:admin', '@outcome:failure'],
  }, async ({ page }) => {
    await setupApi(page, { pdfFailure: true })
    await openCatalog(page)
    await openSelection(page, 'pdf')
    await page.getByTestId('additional-selection-submit').click()
    await expect(page.getByText('No se pudo generar el PDF.')).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Preparar PDF' })).toBeVisible()
  })
})
