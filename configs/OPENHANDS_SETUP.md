# OpenHands Setup

OpenHands is an optional autonomous development workspace. Use it for exploration, terminal/browser experimentation, and agentic repo tasks when you want a full existing agent platform.

## Windows Notes

Current OpenHands docs recommend Docker Desktop on Windows with WSL 2 enabled. The Docker command should be run inside WSL. Do not install Docker Desktop or WSL automatically without approval.

Docs checked:

- OpenHands local setup: `https://docs.openhands.dev/openhands/usage/run-openhands/local-setup`
- OpenHands local LLMs: `https://docs.openhands.dev/openhands/usage/llms/local-llms`

## Local Ollama Configuration

After launching OpenHands, open Settings -> LLM and use advanced options:

- Custom Model: `openai/qwen2.5-coder:14b`
- Base URL: `http://host.docker.internal:11434/v1`
- API Key: `local-llm`

OpenHands docs note that for local LLM servers without auth, any placeholder key can be used.

## Safety Rules

- Use disposable repo first.
- Do not mount your whole drive.
- Mount only the selected repo/workspace.
- Do not paste secrets.
- Do not enable broad GitHub automation until reviewed.
- Keep local Ollama as default for experiments.

## Scripts

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\install-openhands-notes.ps1
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\health-openhands.ps1
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-openhands.ps1
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\stop-openhands.ps1
```

If Docker is missing, start script will stop and explain the blocker.
