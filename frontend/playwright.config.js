import { defineConfig, devices } from '@playwright/test';
import { PANEL_VIEWPORTS } from './config/responsive.js';

const PORT = process.env.E2E_PORT ? Number(process.env.E2E_PORT) : 3000;
const baseURL = process.env.E2E_BASE_URL || `http://localhost:${PORT}`;
const reuseExistingServer = !process.env.CI;
const isResponsiveRun = process.env.E2E_RESPONSIVE === '1';

const responsiveProjects = Object.entries(PANEL_VIEWPORTS).map(([name, viewport]) => ({
  name: `responsive-${name}`,
  use: {
    ...devices['Desktop Chrome'],
    viewport,
    hasTouch: ['compact', 'portrait', 'landscape'].includes(name),
    isMobile: name === 'compact',
  },
}));

export default defineConfig({
  globalSetup: './e2e/global-setup.js',
  testDir: './e2e',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: true,
  retries: process.env.CI ? 2 : 1,
  workers: 3,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['json', { outputFile: 'e2e-results/results.json' }],
    ['./e2e/reporters/flow-coverage-reporter.mjs', { outputDir: 'e2e-results' }],
  ],
  use: {
    baseURL,
    navigationTimeout: 60_000,
    trace: 'retain-on-failure',
    screenshot: 'off',
    video: 'off',
  },
  webServer: {
    command: `npm run dev -- --host 127.0.0.1 --port ${PORT} --strictPort`,
    url: baseURL,
    reuseExistingServer,
    timeout: 120_000,
  },
  projects: isResponsiveRun
    ? responsiveProjects
    : [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
