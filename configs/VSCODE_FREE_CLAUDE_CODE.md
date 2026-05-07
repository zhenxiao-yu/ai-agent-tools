# VS Code Local AI Setup

## Open VS Code

```powershell
code
```

## Confirm Cline

Open Extensions and search for Cline. On this machine the installed extension ID is:

```text
saoudrizwan.claude-dev
```

Extension IDs can change. Verify the installed extension in the VS Code Extensions panel if settings look different.

## Cline Directly With Ollama

This is the simplest local setup.

- Provider: `Ollama`
- Base URL: `http://localhost:11434`
- Model: `qwen2.5-coder:14b`

Use Cline for supervised PM, Tech Lead, QA, Reviewer, DevOps, debugging, and browser-assisted workflows.

## Claude Code Local Proxy Mode

Start the proxy:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-free-claude-code-proxy.ps1
```

Use these local-only values for Claude Code-compatible tools:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:8082
ANTHROPIC_AUTH_TOKEN=freecc
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
```

Do not append `/v1` to `ANTHROPIC_BASE_URL`.

If a VS Code Claude Code extension supports environment variables, configure those values in the extension environment. Do not store real Anthropic keys for local mode.

## Which Tool To Use

- Cline + Ollama: easiest VS Code local assistant.
- Aider + Ollama: best terminal branch worker for focused edits.
- free-claude-code + Ollama: compatibility layer for Claude Code-style tools.

Local models are not real Claude. Keep tasks small, validate everything, and review before committing.
