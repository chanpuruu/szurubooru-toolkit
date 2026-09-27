import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  use: {
    baseURL: 'http://127.0.0.1:8081',
    trace: 'retain-on-failure',
    channel: process.env.PLAYWRIGHT_CHANNEL,
  },
  webServer: {
    command: 'uv run --extra web --no-sync python -m szurubooru_toolkit.web --port 8081',
    cwd: '..',
    env: { TOOLKIT_WEB_STATIC_DIR: 'frontend/dist' },
    url: 'http://127.0.0.1:8081/readyz',
    reuseExistingServer: false,
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
})