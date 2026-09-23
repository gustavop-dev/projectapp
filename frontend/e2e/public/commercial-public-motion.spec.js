import { test, expect } from '../helpers/test.js'
import { PANEL_VIEWPORTS } from '../../config/responsive.js'
import { commercialModule, commercialPages, setupCommercialPublic, openCommercial } from '../helpers/commercial-public.js'

test.setTimeout(60_000)
test.use({ viewport: PANEL_VIEWPORTS.compact })

const categories = [
  {
    slug: 'marketing', name: 'Marketing',
    modules: Array.from({ length: 8 }, (_, index) => ({ ...commercialModule, slug: `landing-${index}`, name: `Landing ${index + 1}` })),
  },
  { slug: 'automation', name: 'Automatización', modules: [commercialModule] },
]

async function openCatalog(page) {
  await setupCommercialPublic(page, { categories })
  await page.addInitScript(() => {
    window.sectionEntrances = []
    document.addEventListener('animationstart', (event) => {
      if (event.animationName === 'public-document-enter') window.sectionEntrances.push(event.target.id)
    })
  })
  await openCommercial(page, commercialPages[0])
}

test('animates a loaded category only on its first entrance', {
  tag: ['@flow:public-additional-modules-theme', '@outcome:success', '@role:guest'],
}, async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await openCatalog(page)
  const category = page.getByRole('region', { name: 'Automatización' })

  await page.getByRole('link', { name: 'Automatización', exact: true }).click()

  await expect.poll(() => page.evaluate(() => window.sectionEntrances.filter((id) => id === 'category-automation').length)).toBe(1)
  await expect(category).toContainText(commercialModule.summary)
  await page.getByRole('link', { name: 'Marketing', exact: true }).click()
  await page.getByRole('link', { name: 'Automatización', exact: true }).click()
  await expect(category).toBeInViewport()
  await expect(category).toHaveCSS('transform', 'none')
  expect(await page.evaluate(() => window.sectionEntrances.filter((id) => id === 'category-automation').length)).toBe(1)
})

test('keeps category navigation still with reduced motion', {
  tag: ['@flow:public-additional-modules-theme', '@outcome:success', '@role:guest'],
}, async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await openCatalog(page)

  await page.getByRole('link', { name: 'Automatización', exact: true }).click()

  const category = page.getByRole('region', { name: 'Automatización' })
  await expect(category).toBeInViewport()
  await expect(category).toHaveCSS('animation-name', 'none')
  await expect(category).toContainText(commercialModule.summary)
  expect(await page.evaluate(() => window.sectionEntrances)).toEqual([])
})

test('keeps partnership controls fixed while revealing conditions', {
  tag: ['@flow:public-financing-theme', '@outcome:success', '@role:guest'],
}, async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await setupCommercialPublic(page)
  await page.addInitScript(() => {
    window.conditionEntrances = 0
    document.addEventListener('animationstart', (event) => {
      if (event.animationName === 'public-document-enter' && event.target.getAttribute('aria-labelledby') === 'financing-conditions-title') {
        window.conditionEntrances += 1
      }
    })
  })
  await openCommercial(page, commercialPages[2])
  const share = page.getByTestId('financing-share')
  const originalPosition = await share.boundingBox()

  await page.getByRole('link', { name: '01 · 12 meses de financiación', exact: true }).click()

  await expect.poll(() => page.evaluate(() => window.conditionEntrances)).toBe(1)
  await expect(page.getByTestId('financing-condition-financing')).toContainText('A clear commercial condition for the partnership.')
  expect(await share.boundingBox()).toEqual(originalPosition)
})
