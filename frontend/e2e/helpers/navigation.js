export async function waitForNuxtApp(page, { timeout = 45_000 } = {}) {
  await page.locator('#__nuxt > *').first().waitFor({ state: 'attached', timeout });
}
