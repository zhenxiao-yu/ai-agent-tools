# Playwright MCP Setup

Playwright MCP is a Model Context Protocol server that gives AI coding assistants access to a live browser session. Agents can inspect the DOM, click elements, observe navigation, and generate better tests without guessing from screenshots.

Docs checked:

- Microsoft Learn Playwright MCP article
- Playwright MCP install examples

## Install

Official install pattern:

```powershell
npm install -g @playwright/mcp
```

Or run without global install:

```powershell
npx @playwright/mcp
```

Chromium browser support:

```powershell
npx playwright install chromium
```

## With Cline / VS Code

Use Cline MCP settings or marketplace to add a local STDIO server:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp"]
    }
  }
}
```

## Difference From Playwright Tests

- Playwright tests are repo validation scripts.
- Playwright MCP is an agent tool for inspecting and controlling a browser.

## Safety

- Use on local/dev URLs first.
- Do not enter secrets into pages while agents are observing.
- Approve tool calls in Cline.
- Do not expose browser sessions publicly.
