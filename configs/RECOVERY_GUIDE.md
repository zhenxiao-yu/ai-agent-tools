# Recovery Guide

Use this when Local AI Mission Control shows a warning or failure. These fixes are safe defaults and avoid commits, pushes, paid APIs, and secrets.

## Ollama Not Working

Symptoms: dashboard says Ollama offline or local model server not responding.

Safe fix:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-local-model-stack.ps1
```

Do not uninstall Ollama or delete models.

## Model Missing

Symptoms: `qwen2.5-coder:14b` is missing.

Safe fix:

```powershell
ollama pull qwen2.5-coder:14b
```

Do not pull huge models unless you approve the disk/time cost.

## Proxy Not Working

Symptoms: free-claude-code proxy offline at port 8082.

Safe fix:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-free-claude-code-proxy.ps1
```

Do not expose port 8082 publicly.

## Dashboard Not Opening

Symptoms: browser cannot open `http://127.0.0.1:8501`.

Safe fix:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\start-dashboard.ps1
```

Log: `C:\ai-agent-tools\logs\dashboard-start.log`

## GitHub CLI Not Logged In

Symptoms: GitHub pipeline checks fail or `gh auth status` says not logged in.

Manual fix:

```powershell
gh auth login
```

Choose GitHub.com, HTTPS, login with browser.

## Repo Dirty

Symptoms: worker refuses to run because repo has uncommitted changes.

Manual checks:

```powershell
git status
git diff
git add .
git commit -m "save work before AI run"
git stash push -m "manual stash before AI run"
```

Do not auto-discard changes.

## Worker Failed

Symptoms: latest worker log contains ERROR or nonzero validation.

Safe fix: open latest worker log, run reviewer, then decide manually.

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-ai-reviewer.ps1 -RepoPath "C:\path\to\repo"
```

## Scheduled Worker Failed

Symptoms: scheduled task exists but latest worker log failed.

Safe fix: disable schedule until the repo is clean and dry-run passes.

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\remove-scheduled-web-worker.ps1
```

## Disable Scheduled Worker

Emergency stop:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\remove-scheduled-web-worker.ps1
```

## Provider Key Missing

Symptoms: provider card says key missing.

Set key:

```powershell
setx DEEPSEEK_API_KEY "YOUR_KEY"
```

Do not paste keys into repos or prompts.

## Provider API Failing

Likely causes: bad key, wrong base URL, wrong model, network, billing/credits.

Safe fix: verify provider dashboard, then run one tiny manual test.

## Node Version Mismatch

Symptoms: package engines require another Node version.

Manual fix: use Volta or nvm-windows. Do not auto-change Node globally.

## Validation Failed

Symptoms: lint/typecheck/build/test failed.

Safe next task: ask AI to fix exactly one validation error, or fix manually.

## Playwright Failed

Symptoms: e2e logs mention screenshots or videos.

Open the Playwright report or artifact paths. Do not delete artifacts until reviewed.

## Emergency Stop

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\remove-scheduled-web-worker.ps1
```
