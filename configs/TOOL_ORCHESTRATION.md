# Tool Orchestration

The dashboard is mission control. It should launch, monitor, gate, route, summarize, recover, and display logs/reports. It should not rebuild full agent products that already exist.

## Roles

- Dashboard: mission control, monitoring, safety gates, logs, reports, repo allowlist, provider health, recovery.
- OpenHands: optional out-of-box autonomous dev workspace for agentic repo tasks, terminal/browser work, and experiments.
- Cline: VS Code interactive coding agent with approval-driven terminal/browser actions and MCP client support.
- Aider: Git-aware code editing worker for focused branch-based changes.
- Aider Browser UI: optional browser UI for manual Aider sessions on local Git repos.
- Playwright MCP: browser automation and structured page inspection for agents.
- free-claude-code: Claude Code-compatible local proxy to Ollama/local/compatible models.
- Ollama: free local model runtime.
- GitHub CLI: issues, PRs, Actions, and pipeline logs.
- Scheduled worker: safe local-only periodic worker with locks, logs, reports, and no push/commit.

## Recommended Routing

- Planning / exploration: OpenHands or Cline
- VS Code interactive edits: Cline
- Focused code edits: Aider
- Scheduled safe work: `run-web-ai-worker.ps1`
- Browser checks: Playwright / Playwright MCP
- Pipeline checks: GitHub CLI
- Claude Code-style local workflow: free-claude-code proxy
- Monitoring and recovery: dashboard

## What Stays Custom

- Safety gates
- Repo allowlist
- Scheduled local worker
- Logs/reports dashboard
- Provider key presence checks
- Recovery / diagnostic bundle

## What Not To Duplicate

Do not rebuild OpenHands, Cline, Aider, Playwright, GitHub Actions, Ollama, or Claude Code protocol compatibility inside Streamlit.
