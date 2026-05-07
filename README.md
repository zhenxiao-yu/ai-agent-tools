# Local AI Agent Tools

This folder contains a conservative local AI coding workflow for Windows web-app development. It is designed to keep working after paid Codex or Claude limits expire by using Ollama, local coding models, Cline, Aider, GitHub CLI, Playwright, and PowerShell scripts.

The system is intentionally small and traceable: inspect, choose one small task, branch, edit, validate, report, review, stop.

## Tool Roles

- Ollama: runs local models such as qwen2.5-coder:14b.
- Cline: supervised PM, Tech Lead, QA, Reviewer, DevOps, and browser/debugging workflows inside VS Code.
- Aider: focused Developer AI for small code edits on an AI branch.
- GitHub CLI: inspects issues, PRs, and GitHub Actions logs.
- Playwright: browser smoke checks for web apps.
- PowerShell scripts: repeatable branch-based automation, reports, logs, and scheduled runs.

## Daily Workflow

1. Pick a repo.
2. Make sure your human work is committed or stashed.
3. Run one worker pass.
4. Review the report and diff.
5. Run the reviewer script.
6. Commit only if you approve.

## 24/7 Scheduled Workflow

Scheduled mode runs one small branch-based worker pass per interval. It does not run an infinite loop, commit, push, or merge.

Scheduled mode is disabled until you install the Windows Scheduled Task. It also requires the exact repo path to be listed in `C:\ai-agent-tools\configs\repo-allowlist.txt`.

Do not point scheduled mode at a broad folder. It does not scan your GitHub folder and does not run across all repos by default. Multi-repo automation requires an explicit approved list.

Install:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\install-scheduled-web-worker.ps1 -RepoPath "C:\path\to\my\web-app" -BaseBranch "main" -IntervalHours 2
```

Disable:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\remove-scheduled-web-worker.ps1
```

## Morning Review

```powershell
cd "C:\path\to\my\web-app"
git status
git branch --sort=-committerdate
git diff --stat
git diff
```

Then run:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\morning-review.ps1 -RepoPath "C:\path\to\my\web-app"
```

## Safety Rules

- Never push directly to main or master.
- Never force push.
- Never auto-commit by default.
- Never run on a dirty repo with uncommitted human changes.
- Never modify secrets, .env files, API keys, SSH keys, tokens, credentials, auth config, payment config, production deployment config, database migrations, or private config files.
- Never touch node_modules, dist, build, .next, coverage, .git, cache folders, generated files, or binary artifacts.
- For Unity repos, never touch Library, Temp, Logs, Obj, Build, Builds, scene/prefab/project settings unattended.
- Stop after one small task.

## Add A New Web Repo

1. Run `C:\ai-agent-tools\scripts\audit-web-repo.ps1`.
2. Copy `C:\ai-agent-tools\configs\AGENTS.web.template.md` into the repo as `AGENTS.md` only after approving that change.
3. Run `run-web-ai-worker.ps1 -DryRun`.
4. Run one manual worker pass.
5. Review the diff and reviewer report.
6. Only consider scheduled mode after 2-3 successful manual runs.

See `C:\ai-agent-tools\configs\FIRST_REAL_REPO_CHECKLIST.md`.

## Node Versions

The worker prints current Node/npm versions and warns when `package.json` has an obvious `engines.node` conflict. It does not change Node versions automatically.

If a repo needs Node 18, 20, 22, or another version, use a tool such as nvm-windows or Volta after approving that change.

## One-Off Worker Pass

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-web-ai-worker.ps1 -RepoPath "C:\path\to\my\web-app" -BaseBranch "main"
```

Dry run:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-web-ai-worker.ps1 -RepoPath "C:\path\to\my\web-app" -BaseBranch "main" -DryRun
```

No-edit audit:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\audit-web-repo.ps1 -RepoPath "C:\path\to\my\web-app"
```

## GitHub Pipeline Logs

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\check-github-pipelines.ps1 -RepoPath "C:\path\to\my\web-app"
```

## Review, Commit, Or Discard

Keep good changes:

```powershell
git add .
git commit -m "AI-assisted maintenance pass"
```

Discard bad changes:

```powershell
git restore .
git checkout main
git branch -D BRANCH_NAME
```

## Paid And Local Model Mix

Use paid Codex or Claude when available for architecture, hard debugging, risky refactors, and high-context reviews. Use local models for small validation-driven tasks: lint fixes, TypeScript fixes, README updates, tiny component polish, and smoke tests.

## Tips For Small Local Models

- Keep tasks small.
- Make one change per run.
- Validate everything.
- Avoid huge context.
- Use `AGENTS.md`.
- Use the task queue.
- Run a reviewer pass before committing.

## Free Claude Code Local Mode

`free-claude-code` is a local compatibility proxy for Claude Code-style clients. In this setup it routes requests to Ollama and `qwen2.5-coder:14b`. It is not real Anthropic Claude, and no paid API keys are required for Ollama mode.

Start local stack:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-local-model-stack.ps1
```

Health check:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\health-local-ai-stack.ps1
```

Start proxy:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-free-claude-code-proxy.ps1
```

Test proxy:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\test-free-claude-code-proxy.ps1
```

Start Claude Code local mode:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-claude-code-local.ps1
```

Enable auto-start:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\enable-local-ai-autostart.ps1
```

Disable auto-start:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\disable-local-ai-autostart.ps1
```

VS Code local setup:

- Cline direct local mode: Provider `Ollama`, Base URL `http://localhost:11434`, Model `qwen2.5-coder:14b`.
- Claude Code compatibility mode: start the proxy, then use `ANTHROPIC_BASE_URL=http://127.0.0.1:8082` and `ANTHROPIC_AUTH_TOKEN=freecc` in the local client environment.

Use Cline + Ollama for the simplest VS Code flow, Aider + Ollama for branch-based terminal edits, and free-claude-code + Ollama only when a Claude Code-style client needs an Anthropic-compatible local endpoint.

Troubleshooting:

- Run the health check first.
- Confirm Ollama responds at `http://127.0.0.1:11434`.
- Confirm the proxy responds at `http://127.0.0.1:8082/v1/models`.
- Do not append `/v1` to `ANTHROPIC_BASE_URL` for Claude Code.
- Keep tasks small because local models are weaker than paid frontier models.

## Performance Tools

Useful lightweight CLI tools:

- `rg`: fast text search.
- `fd`: fast file search.
- `jq`: JSON inspection.
- `bat`: readable file viewing.
- `delta`: readable git diffs.
- `pnpm`: package manager through Corepack.

Validate:

```powershell
rg --version
fd --version
jq --version
bat --version
delta --version
pnpm --version
```

If a tool was installed by `winget` but is not visible yet, open a new terminal so PATH refreshes.

## Repo Health And Validation

Repo health scan:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\repo-health-scan.ps1 -RepoPath "C:\path\to\my\web-app"
```

Validation runner:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\repo-validation-runner.ps1 -RepoPath "C:\path\to\my\web-app"
```

AI stack monitor:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\ai-stack-monitor.ps1
```

Watch mode:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\ai-stack-monitor.ps1 -Watch
```

## Dashboard

Start the local dashboard:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-dashboard.ps1
```

Open the dashboard, starting it only if needed:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-dashboard.ps1
```

Open:

```text
http://127.0.0.1:8501
```

Create desktop and Start Menu shortcuts:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\create-dashboard-shortcut.ps1
```

The dashboard reads explicit repo paths from `C:\ai-agent-tools\configs\repo-allowlist.txt`. It does not scan your whole disk, does not enable scheduled mode, does not commit, and does not push.

See `C:\ai-agent-tools\configs\DASHBOARD_SETUP.md`.

Dashboard pages:

- Home
- Fix Center
- Tools / Integrations
- Workflow Wizard
- Projects
- Vibe Code
- Runs
- Morning Review
- Scheduler
- Models
- Providers
- Logs & Reports
- VS Code
- Settings
- Help

The dashboard is designed for free local multi-project vibe coding: dry-run first, one small AI branch, validation, report, human review.

Fix Center:

```text
Open the dashboard -> Fix Center
```

Create a non-secret diagnostic bundle:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\make-diagnostic-bundle.ps1
```

Recovery guide:

```text
C:\ai-agent-tools\configs\RECOVERY_GUIDE.md
```

## Tool Orchestration

The dashboard is mission control, not a replacement for existing agent tools.

Use:

- OpenHands for optional autonomous dev workspace experiments.
- Cline for VS Code interactive agent work.
- Aider for Git-aware focused edits.
- Aider Browser UI for manual browser-based Aider sessions.
- Playwright MCP for browser automation tools.
- free-claude-code for Claude Code-compatible local mode.
- Ollama for local/free models.
- GitHub CLI for Actions/issues/PRs.

Docs:

```text
C:\ai-agent-tools\configs\TOOL_ORCHESTRATION.md
C:\ai-agent-tools\configs\WHAT_NOT_TO_REBUILD.md
```

## VS Code Control Center

Open the Local AI Control Center workspace:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-ai-tools-vscode.ps1
```

Open VS Code and dashboard together:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\open-ai-tools-vscode.ps1 -OpenDashboard
```

Run the full local doctor check:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\doctor-local-ai.ps1
```

Inside VS Code, use `Tasks: Run Task` and choose an `AI:` task.

See `C:\ai-agent-tools\configs\VSCODE_WORKFLOW.md`.

## Chinese And Payment-Friendly Providers

Optional paid provider hooks live in:

```text
C:\ai-agent-tools\configs\providers
C:\ai-agent-tools\configs\model-profiles.json
```

Provider health:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\provider-health.ps1
```

Manage provider keys without printing them:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\manage-provider-secrets.ps1 -Action List
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\manage-provider-secrets.ps1 -Action Set -Provider deepseek
```

Test one provider:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\test-provider-model.ps1 -ProviderName deepseek -BaseUrl "https://api.deepseek.com" -Model "deepseek-chat" -ApiKeyEnvVar DEEPSEEK_API_KEY
```

Compare local and configured providers:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\compare-models.ps1
```

Manual paid worker:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-web-ai-worker-paid.ps1 -RepoPath "C:\path\to\repo" -BaseBranch "main" -ProviderName deepseek -BaseUrl "https://api.deepseek.com" -Model "deepseek-chat" -ApiKeyEnvVar DEEPSEEK_API_KEY
```

Paid providers may cost money. Do not schedule paid provider workers by default.
