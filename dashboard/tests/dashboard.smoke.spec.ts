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

    await page.getByRole("radiogroup", { name: /Navigate/i }).getByText("Automation", { exact: false }).click();
    await expect(page.getByText("Recommended Route")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Agent Flow")).toBeVisible({ timeout: 20_000 });

    await page.getByRole("radiogroup", { name: /Navigate/i }).getByText("Models", { exact: false }).click();
    await expect(page.getByText("Model Selector")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Installed Models")).toBeVisible({ timeout: 20_000 });

    expect(
      consoleErrors.filter((entry) => !entry.includes("favicon")).length,
      `Unexpected browser console errors: ${consoleErrors.join("\n")}`
    ).toBe(0);
  });
});
