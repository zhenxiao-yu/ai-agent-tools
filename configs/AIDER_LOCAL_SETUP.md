# Aider Local Setup

Aider is the Developer AI for focused code edits.

## Basic Command

```powershell
aider --model ollama/qwen2.5-coder:14b
```

If `aider` is not on PATH, use the installed full path:

```powershell
C:\Users\YZX06\.local\bin\aider.exe --model ollama/qwen2.5-coder:14b
```

The worker script resolves Aider automatically by checking PATH and `C:\Users\YZX06\.local\bin\aider.exe`.

## With Validation

```powershell
aider --model ollama/qwen2.5-coder:14b --test-cmd "npm run build"
```

If scripts exist:

```powershell
aider --model ollama/qwen2.5-coder:14b --test-cmd "npm run lint && npm run typecheck && npm run build"
```

## Rules

- Use Aider on AI branches only.
- Disable auto-commit for unattended runs.
- Do not push automatically.
- Review diffs before commit.
- Keep one task per run.
- Avoid dependency upgrades unless you explicitly approve them.
- Do not edit secrets, auth, payments, deployment config, or migrations.
