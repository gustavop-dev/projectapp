import { defineConfig, devices } from '@playwright/test'

const python = process.env.CAPTCHA_TEST_PYTHON || 'python3'
const quotedPython = "'" + python.replaceAll("'", "'\\''") + "'"

export default defineConfig({
  testDir: './e2e',
  testMatch: ['captcha/*.spec.js'],
  timeout: 60_000,
  expect: { timeout: 15_000 },
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:3199', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium-captcha', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: `${quotedPython} ../backend/projectapp/tests/captcha_server.py`,
      url: 'http://127.0.0.1:3198/__captcha_ready__',
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 3199 --strictPort',
      url: 'http://127.0.0.1:3199',
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        DJANGO_DEV_TARGET: 'http://127.0.0.1:3198',
        NUXT_PUBLIC_RECAPTCHA_SITE_KEY: 'browser-test-site-key',
        NUXT_PUBLIC_RECAPTCHA_ENABLED: 'true',
      },
    },
  ],
})
