# Free Claude Code Local Setup

`free-claude-code` is a local compatibility proxy. It is not Anthropic Claude, and it does not make local models as strong as real Claude. It lets Claude Code-style clients talk to local providers through an Anthropic-compatible API.

This setup routes Claude Code-style traffic to:

- Ollama: `http://localhost:11434`
- Model: `qwen2.5-coder:14b`
- Proxy: `http://127.0.0.1:8082`

No paid API keys are required for Ollama mode.

## Installed Path

```text
C:\ai-agent-tools\free-claude-code
```

The local config is:

```text
C:\ai-agent-tools\free-claude-code\.env
```

It uses `ANTHROPIC_AUTH_TOKEN=freecc` only as a local proxy token. Do not use real Anthropic keys in this file.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-free-claude-code-proxy.ps1
```

## Stop

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\stop-local-model-stack.ps1
```

This stops the proxy started by these scripts and leaves Ollama running.

## Test

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\test-free-claude-code-proxy.ps1
```

## Claude Code CLI Local Environment

Use session-scoped variables only:

```powershell
$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:8082"
$env:ANTHROPIC_AUTH_TOKEN = "freecc"
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY = "1"
```

The launcher script sets these only for that PowerShell process:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-claude-code-local.ps1
```

## Security Notes

- The proxy is bound to localhost by these scripts.
- Web server tools are disabled in the local `.env`.
- Raw payload and raw event logging are disabled.
- No paid provider keys are stored.
- Do not expose port `8082` outside your machine.

## Known Limitations

- Local models are weaker than real Claude for architecture, long-context debugging, and subtle reviews.
- Claude Code CLI must be installed separately if you want the official CLI experience.
- Cline + Ollama is simpler and does not need this proxy.
- Aider + Ollama remains the best terminal workflow for focused code edits.

## When To Use It

- You want Claude Code-compatible tooling to talk to local Ollama.
- You want session-scoped `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` without touching real Anthropic settings.
- You want to test Claude Code-style workflows while staying local/free.

## When Not To Use It

- For normal VS Code chat/editing: use Cline + Ollama.
- For focused Git-aware edits: use Aider + Ollama.
- For scheduled maintenance: use the existing local worker.
- For deep architecture: use supervised stronger models when available.

Local model quality is the limiting factor. The proxy changes protocol compatibility, not reasoning strength.
