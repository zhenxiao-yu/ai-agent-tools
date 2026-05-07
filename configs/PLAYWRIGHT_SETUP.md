# Playwright Setup

Use Playwright for browser-level smoke checks in web apps.

## Install In A Repo

```powershell
npm install -D @playwright/test
npx playwright install
```

Add this package.json script when approved:

```json
{
  "scripts": {
    "e2e": "playwright test"
  }
}
```

## Common Local URLs

- Vite: http://localhost:5173
- Next.js: http://localhost:3000

## Smoke Test Intent

A minimal smoke test should check:

- body is visible
- page is not a 404
- page does not show "Internal Server Error"

Do not automatically modify every repo. Add Playwright per project when it is useful and approved.
