# AGENTS.md

## Project Intent
AI Agent Tools is a Windows-first toolkit for local-first AI coding workflows. Prioritize conservative automation, traceable changes, and human-reviewed execution.

## Preferred Agent Workflow
1. Planner: inspect the relevant scripts, configs, and docs before proposing changes.
2. Builder: own a small file set, keep diffs readable, and avoid broad rewrites unless requested.
3. Reviewer: verify the affected workflow end to end and confirm safety assumptions still hold.

## Setup
```powershell
git clone https://github.com/zhenxiao-yu/ai-agent-tools.git
cd ai-agent-tools
powershell -ExecutionPolicy Bypass -File scripts/start-local-model-stack.ps1
powershell -ExecutionPolicy Bypass -File scripts/open-dashboard.ps1
```

## Validation
```powershell
powershell -ExecutionPolicy Bypass -File scripts/doctor-local-ai.ps1
```
Run any repo-specific smoke checks for the feature you changed before opening a PR.

## Guardrails
- Never commit secrets, provider keys, or filled `.env` files.
- Do not automate pushes to `main` or `master`.
- Prefer branch-isolated, reviewable changes over autonomous large-batch edits.
- Keep Windows paths, PowerShell behavior, and local-model assumptions explicit in docs.
- Update docs when scripts, setup steps, or dashboard behavior change.

## Release Hygiene
- Treat releases as human-reviewed milestones.
- Document breaking workflow changes in the README and release notes.
- Keep generated reports, session logs, and local tool state out of git.