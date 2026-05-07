# VS Code Workflow

Open the tools workspace:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-ai-tools-vscode.ps1
```

Open the workspace and dashboard together:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-ai-tools-vscode.ps1 -OpenDashboard
```

Workspace file:

```text
C:\ai-agent-tools\Local AI Control Center.code-workspace
```

## Run Tasks

In VS Code:

1. Open Command Palette.
2. Run `Tasks: Run Task`.
3. Pick one:
   - `AI: Open Dashboard`
   - `AI: Health Check`
   - `AI: Stack Monitor`
   - `AI: Provider Health`
   - `AI: Test Proxy`
   - `AI: Compare Models Local Only`

## Recommended Extensions

- `ms-vscode.powershell`
- `saoudrizwan.claude-dev`
- `anthropic.claude-code`
- `dbaeumer.vscode-eslint`
- `esbenp.prettier-vscode`

## Doctor Check

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\doctor-local-ai.ps1
```

The doctor writes a report under:

```text
C:\ai-agent-tools\reports
```

## Cline Local Mode

Use Cline directly with Ollama:

- Provider: `Ollama`
- Base URL: `http://localhost:11434`
- Model: `qwen2.5-coder:14b`

This is the simplest VS Code local model flow.
