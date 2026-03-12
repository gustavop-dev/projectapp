import { execSync } from 'child_process';

/**
 * Playwright globalSetup — ensures Chromium is installed before any test runs
 * and pre-warms the Nuxt dev server so first-visit compilation doesn't cause timeouts.
 */
export default async function globalSetup() {
  execSync('npx playwright install chromium', { stdio: 'inherit' });

  // Pre-warm the dev server to trigger route compilation before tests start
  const PORT = process.env.E2E_PORT ? Number(process.env.E2E_PORT) : 5173;
  const baseURL = process.env.E2E_BASE_URL || `http://localhost:${PORT}`;
  const warmupRoutes = ['/', '/proposal/warmup-prefetch'];
  for (const route of warmupRoutes) {
    try {
      await fetch(`${baseURL}${route}`).catch(() => {});
    } catch (_e) { /* ignore — server may not be ready yet */ }
  }
}
