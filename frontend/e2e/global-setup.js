import { execSync } from 'child_process';

/**
 * Playwright globalSetup — ensures Chromium is installed before any test runs.
 * Runs without --quiet since this Playwright version does not support it.
 */
export default async function globalSetup() {
  execSync('npx playwright install chromium', { stdio: 'inherit' });
}
