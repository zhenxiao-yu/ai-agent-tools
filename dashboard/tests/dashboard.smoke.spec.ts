import { expect, test } from "@playwright/test";

test.describe("Local AI Mission Control", () => {
  test("renders the main dashboard and key pages", async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto("/");

    await expect(page.getByText("Local AI Mission Control")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText("Plug-and-Play Workflow")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText("failed to render")).toHaveCount(0);
    await expect(page.locator('section[data-testid="stSidebar"]').getByText('<div class="status-row">')).toHaveCount(0);
    await expect(page.getByText("Repository Setup")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Local AI", { exact: true })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText('<div class="card-kicker">')).toHaveCount(0);
    await expect(page.locator('section[data-testid="stSidebar"]').getByRole("button", { name: "Automation" })).toHaveCount(0);
    await expect(page.locator('section[data-testid="stSidebar"]').getByRole("button", { name: "Models" })).toHaveCount(0);
    await expect(page.locator('section[data-testid="stSidebar"]').getByRole("button", { name: "Providers" })).toHaveCount(0);
    await expect(page.locator('section[data-testid="stSidebar"]').getByRole("button", { name: "Settings" })).toHaveCount(0);

    await page.getByRole("radiogroup", { name: /Navigate/i }).getByText("Automation", { exact: false }).click();
    await expect(page.getByText("Recommended Route")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Agent Flow")).toBeVisible({ timeout: 20_000 });

    await page.getByRole("radiogroup", { name: /Navigate/i }).getByText("Models", { exact: false }).click();
    await expect(page.getByText("Model Selector")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Advanced Runtime Output")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Default local coding model")).toBeVisible({ timeout: 20_000 });

    await page.getByRole("radiogroup", { name: /Navigate/i }).getByText("Providers", { exact: false }).click();
    await expect(page.getByText("Manage paid API keys for turbo mode")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Never store API keys here. Use the Providers page.")).toHaveCount(0);

    await page.getByRole("radiogroup", { name: /Navigate/i }).getByText("Settings", { exact: false }).click();
    await expect(page.getByText("Configure dashboard defaults")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Never store API keys here. Use the Providers page.")).toBeVisible({ timeout: 20_000 });

    expect(
      consoleErrors.filter((entry) => !entry.includes("favicon")).length,
      `Unexpected browser console errors: ${consoleErrors.join("\n")}`
    ).toBe(0);
  });
});
