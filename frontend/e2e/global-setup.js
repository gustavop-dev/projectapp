import { execSync } from 'child_process';
import { chromium } from '@playwright/test';
import { waitForNuxtApp } from './helpers/navigation.js';

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
    '/en-us/panel/projects',
    '/en-us/panel/accounting/hostings',
    '/en-us/panel/accounting/incomes',
    '/en-us/panel/accounting/collections',
    '/en-us/platform/login',
    '/en-us/platform/dashboard',
    '/en-us/platform/projects',
    '/en-us/platform/projects/1',
    '/en-us/platform/projects/1/board',
    '/panel/login',                         // SPA — admin panel login
    '/panel',                               // SPA — admin dashboard
    '/panel/admins',                        // SPA — admin management
    '/es-co/panel/additional-modules',      // SPA — reusable sales catalog
    '/panel/blog',                          // SPA — blog list
    '/panel/blog/create',                   // SPA — blog create
    '/panel/blog/1/edit',                   // SPA — blog edit (dynamic)
    '/panel/blog/calendar',                 // SPA — blog calendar
    '/panel/clients',                       // SPA — client list
    '/panel/communications',                // SPA — client communications registry
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
    '/es-co/panel/proposals',               // SPA — proposals list
    '/panel/proposals/create',              // SPA — create proposal
    '/panel/proposals/999/edit',            // SPA — edit proposal (dynamic)
    '/panel/proposals/defaults',            // SPA — proposal defaults
    '/panel/proposals/email-deliverability', // SPA — email deliverability
    '/panel/tasks',                         // SPA — task list
    '/panel/views',                         // SPA — admin view map
    '/proposal/warmup-prefetch',            // SPA — proposal viewer
    '/diagnostic/warmup-prefetch',          // SPA — diagnostic public viewer
    '/es-co/additional-modules',            // SSR — public additional modules catalog
    '/es-co/additional-modules/share/11111111-1111-4111-8111-111111111111', // SPA — shared catalog
    '/blog',                                // SSR — public blog list
    '/landing-apps',                        // SSR — landing apps page
    '/landing-software',                    // SSR — landing software page
    '/landing-web-design',                  // SSR — landing web design page
  ];

  const requiredWarmupRoutes = new Set([
    '/en-us/panel/projects',
    '/en-us/panel/accounting/hostings',
    '/en-us/panel/accounting/incomes',
    '/en-us/panel/accounting/collections',
    '/en-us/platform/login',
    '/en-us/platform/projects/1',
  ]);
  const warmupFailures = [];

  let browser;
  try {
    browser = await chromium.launch();
    const page = await browser.newPage();
    await page.addInitScript(() => {
      const admin = {
        id: 9001,
        user_id: 9001,
        email: 'admin@e2e-test.com',
        role: 'admin',
        is_staff: true,
        is_superuser: true,
        is_onboarded: true,
        profile_completed: true,
      };
      localStorage.setItem('access_token', 'e2e-warmup-panel-token');
      localStorage.setItem('refresh_token', 'e2e-warmup-panel-refresh');
      localStorage.setItem('user', JSON.stringify(admin));
      localStorage.setItem('platform_access_token', 'e2e-warmup-platform-token');
      localStorage.setItem('platform_refresh_token', 'e2e-warmup-platform-refresh');
      localStorage.setItem('platform_user', JSON.stringify(admin));
    });
    await page.route('**/api/auth/check/', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        user: { username: 'admin', is_staff: true, is_superuser: true },
      }),
    }));
    await page.route('**/api/accounts/me/', (route) => route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 9001,
        user_id: 9001,
        email: 'admin@e2e-test.com',
        role: 'admin',
        is_onboarded: true,
        profile_completed: true,
      }),
    }));
    for (const route of warmupRoutes) {
      const isRequired = requiredWarmupRoutes.has(route);
      try {
        await page.goto(`${baseURL}${route}`, {
          timeout: isRequired ? 45_000 : 10_000,
          waitUntil: 'domcontentloaded',
        });
        if (isRequired) await waitForNuxtApp(page);
      } catch (error) {
        if (isRequired) {
          const message = error instanceof Error ? error.message : String(error);
          warmupFailures.push(`${route}: ${message}`);
        }
      }
    }
    await page.close();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    warmupFailures.push(`browser: ${message}`);
  } finally {
    if (browser) await browser.close();
  }

  if (warmupFailures.length > 0) {
    throw new Error(`Required Nuxt warmup failed:\n${warmupFailures.join('\n')}`);
  }
}
