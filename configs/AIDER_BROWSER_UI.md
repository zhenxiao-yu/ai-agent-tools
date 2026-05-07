# Aider Browser UI

Aider Browser UI is an optional browser interface for manual Aider sessions on local Git repos.

Docs checked: `https://aider.chat/docs/usage/browser.html`

## Difference From Scheduled Worker

- Scheduled worker: one safe local pass, logs/report, no auto-commit/push.
- Aider Browser UI: interactive manual session that can edit files. Aider docs note browser UI can directly edit files and may commit changes depending on mode/config.

## Safe Launch

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-aider-browser.ps1 -RepoPath "C:\path\to\repo"
```

The launcher:

- verifies repo exists
- verifies `.git`
- verifies repo is allowlisted
- uses local model `ollama/qwen2.5-coder:14b`
- passes `--no-auto-commits`
- does not push

## When To Use

Use for manual focused coding sessions where you want Aider in a browser instead of the terminal. For unattended runs, use the scheduled worker instead.
