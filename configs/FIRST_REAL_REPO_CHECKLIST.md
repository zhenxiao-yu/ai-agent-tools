# First Real Repo Checklist

## Step 1

Run `audit-web-repo.ps1`.

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\audit-web-repo.ps1 -RepoPath "C:\path\to\my\web-app"
```

## Step 2

Copy `C:\ai-agent-tools\configs\AGENTS.web.template.md` into the repo as `AGENTS.md` only if you approve.

## Step 3

Run `run-web-ai-worker.ps1` with `-DryRun`.

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-web-ai-worker.ps1 -RepoPath "C:\path\to\my\web-app" -BaseBranch "main" -DryRun
```

## Step 4

Run one manual worker pass.

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-web-ai-worker.ps1 -RepoPath "C:\path\to\my\web-app" -BaseBranch "main"
```

## Step 5

Review `git diff`.

## Step 6

Run reviewer.

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-ai-reviewer.ps1 -RepoPath "C:\path\to\my\web-app"
```

## Step 7

Manually commit or discard.

## Step 8

Only after 2-3 successful manual runs, consider scheduled mode.
