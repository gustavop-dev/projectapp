import { test as base, expect } from "@playwright/test";

const shouldLogErrors = process.env.E2E_LOG_ERRORS === "1";
const shouldValidateResponsive = process.env.E2E_RESPONSIVE === "1";

async function assertResponsiveContract(page, testInfo) {
  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    const body = document.body;
    return Math.max(root.scrollWidth, body?.scrollWidth || 0) - root.clientWidth;
  });
  expect(overflow, `La página desborda horizontalmente ${overflow}px en ${testInfo.project.name}`).toBeLessThanOrEqual(1);

  const pathname = new URL(page.url()).pathname;
  if (pathname.includes('/panel') && testInfo.project.use.viewport?.width >= 1920) {
    const contentWidth = await page.locator('.admin-layout main > div').evaluate((element) => (
      element.getBoundingClientRect().width
    ));
    expect(contentWidth, 'El contenido del panel supera 1440px en monitor wide').toBeLessThanOrEqual(1441);
  }

  if (testInfo.project.use.hasTouch) {
    const undersizedTargets = await page.locator('[data-responsive-touch-target]').evaluateAll((elements) => (
      elements
        .filter((element) => {
          const style = getComputedStyle(element);
          const rect = element.getBoundingClientRect();
          return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
        })
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return { label: element.getAttribute('aria-label') || element.textContent?.trim(), width: rect.width, height: rect.height };
        })
        .filter(({ width, height }) => width < 43.5 || height < 43.5)
    ));
    expect(undersizedTargets, 'Hay targets táctiles declarados por debajo de 44px').toEqual([]);
  }
}

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    if (shouldLogErrors) {
      page.on("pageerror", (err) => {
        console.error("[e2e:pageerror]", err);
      });
      page.on("console", (msg) => {
        if (msg.type() === "error") {
          console.error("[e2e:console:error]", msg.text());
        }
      });
    }
    await use(page);
    const isResponsiveTest = testInfo.tags.some((tag) => tag.startsWith('@responsive:'));
    if (shouldValidateResponsive && isResponsiveTest && !page.isClosed() && testInfo.errors.length === 0) {
      await assertResponsiveContract(page, testInfo);
    }
  },
});

export { expect };
