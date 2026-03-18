import { execSync } from 'child_process';
import { chromium } from '@playwright/test';

/**
 * Playwright globalSetup — ensures Chromium is installed before any test runs
 * and pre-warms the Nuxt dev server so first-visit compilation doesn't cause timeouts.
 *
 * SPA routes (ssr: false) need a real browser visit to trigger Vite on-demand
 * compilation — plain HTTP fetch only gets the HTML shell without compiling
 * the client-side route modules.
 */
export default async function globalSetup() {
  execSync('npx playwright install chromium', { stdio: 'inherit' });

  const PORT = process.env.E2E_PORT ? Number(process.env.E2E_PORT) : 3000;
  const baseURL = process.env.E2E_BASE_URL || `http://localhost:${PORT}`;

  // Routes to warm up — includes SSR and SPA routes
  const warmupRoutes = [
    '/',                        // SSR — triggers initial Vite client build
    '/panel/login',             // SPA — admin panel
    '/platform/login',          // SPA — platform module
    '/proposal/warmup-prefetch', // SPA — proposal viewer
  ];

  let browser;
  try {
    browser = await chromium.launch();
    const page = await browser.newPage();
    for (const route of warmupRoutes) {
      try {
        await page.goto(`${baseURL}${route}`, { timeout: 30000, waitUntil: 'load' });
        // Allow Vite to finish on-demand compilation for the route module
        await page.waitForTimeout(1500);
      } catch (_e) { /* ignore — server may not be ready yet */ }
    }
    await page.close();
  } catch (_e) {
    // Browser warmup is best-effort; tests will still compile routes on first visit
  } finally {
    if (browser) await browser.close();
  }
}
