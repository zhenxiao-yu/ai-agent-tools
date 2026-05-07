# Cline MCP Tools

MCP, Model Context Protocol, lets Cline connect to external tools such as browser automation, GitHub, file utilities, or local services.

Docs checked: `https://docs.cline.bot/mcp/adding-and-configuring-servers`

## Cline MCP Support

Cline supports MCP servers through its MCP Servers UI. You can:

- browse the MCP Marketplace
- add servers from GitHub
- configure local STDIO servers
- configure remote/SSE servers
- enable/disable/restart servers

## Useful MCP Servers

- Playwright MCP for browser automation
- GitHub tools if scoped and authenticated safely
- Filesystem/repo tools only with narrow paths

## Safety Rules

- Approve tool calls.
- Do not enable broad filesystem access unless needed.
- Do not paste secrets into MCP config.
- Do not add always-allow rules casually.
- Keep local model + manual approval as default.

## Local Model + MCP

Cline local model:

- Provider: Ollama
- Base URL: `http://localhost:11434`
- Model: `qwen2.5-coder:14b`

Useful prompts:

```text
Use the Playwright MCP tool to inspect this local page.
Use repo validation output instead of guessing.
Run only one safe change.
Do not edit secrets, auth, payment, deployment, or migrations.
```
