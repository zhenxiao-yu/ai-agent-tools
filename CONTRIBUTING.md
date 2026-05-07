# Contributing to AI Agent Tools

Thanks for contributing. This repository is a Windows-first toolkit for local AI coding workflows, so the main contribution standard is safety: small changes, clear docs, and reproducible automation.

## Before You Start

- Read [README.md](README.md), [AGENTS.md](AGENTS.md), and the relevant files in `configs/`.
- For non-trivial workflow changes, open an issue or discussion first.
- Keep changes scoped. Avoid mixing dashboard, prompt, automation, and repo-policy changes in the same PR unless they are tightly related.

## Local Setup

```powershell
git clone https://github.com/zhenxiao-yu/ai-agent-tools.git
cd ai-agent-tools
powershell -ExecutionPolicy Bypass -File scripts/start-local-model-stack.ps1
powershell -ExecutionPolicy Bypass -File scripts/open-dashboard.ps1
```

## Validation

Before opening a PR, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/doctor-local-ai.ps1
```

Also manually verify the workflow you changed. Examples:
- dashboard UI updates: open the dashboard and test the affected page
- setup docs: follow the updated setup steps from scratch
- automation scripts: run the script in a safe local scenario first

## Contribution Rules

- Never commit secrets, tokens, or populated `.env` files.
- Do not add automation that pushes directly to protected branches.
- Keep Windows and PowerShell behavior explicit in docs.
- Prefer readable scripts and reversible automation over clever but opaque flows.
- Update `README.md`, `CHANGELOG.md`, and relevant docs when behavior changes.

## Commit Style

Use clear conventional-style commit messages when possible:

```text
docs: clarify local model setup
fix(dashboard): resolve repo path handling
chore(gitignore): ignore local agent state
```

## Pull Requests

A good PR here includes:
- a short explanation of the workflow being changed
- why the change is needed
- how you validated it
- any screenshots for dashboard/UI work

## Release Notes

If a change affects setup, automation safety, or user-facing workflow behavior, add it to [CHANGELOG.md](CHANGELOG.md).
