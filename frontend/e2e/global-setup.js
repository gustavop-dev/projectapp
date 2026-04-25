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
    '/',                                    // SSR — triggers initial Vite client build
    '/panel/login',                         // SPA — admin panel login
    '/panel',                               // SPA — admin dashboard
    '/panel/admins',                        // SPA — admin management
    '/panel/blog',                          // SPA — blog list
    '/panel/blog/create',                   // SPA — blog create
    '/panel/blog/1/edit',                   // SPA — blog edit (dynamic)
    '/panel/blog/calendar',                 // SPA — blog calendar
    '/panel/clients',                       // SPA — client list
    '/panel/defaults',                      // SPA — defaults
    '/panel/diagnostics',                   // SPA — diagnostics list
    '/panel/diagnostics/create',            // SPA — diagnostic create
    '/panel/diagnostics/defaults',          // SPA — diagnostic defaults
    '/panel/diagnostics/7/edit',            // SPA — diagnostic edit (dynamic)
    '/panel/documents',                     // SPA — documents list
    '/panel/documents/create',              // SPA — document create
    '/panel/documents/1/edit',              // SPA — document edit (dynamic)
    '/panel/emails',                        // SPA — email templates
    '/panel/portfolio',                     // SPA — portfolio list
    '/panel/portfolio/create',              // SPA — portfolio create
    '/panel/portfolio/1/edit',              // SPA — portfolio edit (dynamic)
    '/panel/proposals',                     // SPA — proposals list
    '/panel/proposals/create',              // SPA — create proposal
    '/panel/proposals/999/edit',            // SPA — edit proposal (dynamic)
    '/panel/proposals/defaults',            // SPA — proposal defaults
    '/panel/proposals/email-deliverability', // SPA — email deliverability
    '/panel/tasks',                         // SPA — task list
    '/panel/views',                         // SPA — admin view map
    '/platform/login',                      // SPA — platform login
    '/platform/dashboard',                  // SPA — platform dashboard
    '/platform/projects',                   // SPA — platform projects list
    '/platform/projects/1',                 // SPA — platform project detail (dynamic)
    '/platform/projects/1/board',           // SPA — platform project board (nested dynamic)
    '/proposal/warmup-prefetch',            // SPA — proposal viewer
    '/diagnostic/warmup-prefetch',          // SPA — diagnostic public viewer
    '/blog',                                // SSR — public blog list
    '/landing-apps',                        // SSR — landing apps page
    '/landing-software',                    // SSR — landing software page
    '/landing-web-design',                  // SSR — landing web design page
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
