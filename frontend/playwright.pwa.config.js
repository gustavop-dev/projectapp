import { defineConfig, devices } from '@playwright/test'

const port = 3197
const python = process.env.PWA_TEST_PYTHON || 'python3'
const quotedPython = "'" + python.replaceAll("'", "'\\''") + "'"

export default defineConfig({
  testDir: './e2e',
  testMatch: ['pwa/*.spec.js', 'admin/admin-pwa-install.spec.js'],
  timeout: 60_000,
  expect: { timeout: 15_000 },
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: { baseURL: `http://127.0.0.1:${port}`, trace: 'retain-on-failure' },
  projects: [{ name: 'chromium-pwa', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `${quotedPython} ../backend/projectapp/tests/pwa_server.py --port ${port}`,
    url: `http://127.0.0.1:${port}/__pwa_ready__`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
})
