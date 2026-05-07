import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 45_000,
  retries: 0,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:8512",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "powershell -ExecutionPolicy Bypass -File ../scripts/start-dashboard-smoke.ps1 -Port 8512",
    url: "http://127.0.0.1:8512",
    cwd: __dirname,
    timeout: 120_000,
    reuseExistingServer: true,
  },
});
