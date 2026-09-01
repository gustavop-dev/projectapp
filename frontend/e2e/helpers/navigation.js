export async function waitForNuxtApp(page, { timeout = 45_000 } = {}) {
  await page.locator('#__nuxt > *').first().waitFor({ state: 'attached', timeout });
  await page.waitForFunction(() => {
    const vueApp = document.querySelector('#__nuxt')?.__vue_app__;
    const nuxtApp = vueApp?.config?.globalProperties?.$nuxt;
    return Boolean(nuxtApp) && nuxtApp.isHydrating === false;
  }, null, { timeout });
}
