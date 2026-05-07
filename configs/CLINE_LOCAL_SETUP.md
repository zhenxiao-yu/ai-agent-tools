# Cline Local Setup

Use Cline in VS Code for supervised planning, review, QA, DevOps analysis, and browser/debugging work.

## Provider

- Provider: Ollama
- Base URL: http://localhost:11434
- Model: qwen2.5-coder:14b
- Default model: qwen2.5-coder:14b
- Backup model: deepseek-coder-v2:16b

## Installed Extension

- Actual installed VS Code extension ID on this machine: `saoudrizwan.claude-dev`
- The originally requested ID `cline.cline` was not found during setup.
- Extension IDs can change. Verify in VS Code Extensions if the Cline UI does not appear.

## Open Cline In VS Code

1. Open VS Code.
2. Open the Extensions view and confirm Cline is installed.
3. Open the Cline panel from the Activity Bar, or run `Cline` from the Command Palette.
4. Configure the model provider:
   - Provider: Ollama
   - Base URL: `http://localhost:11434`
   - Model: `qwen2.5-coder:14b`

## Recommended Roles

- Product Manager AI: choose one small useful task.
- Tech Lead AI: turn that task into a tiny implementation plan.
- QA AI: run validation and browser checks.
- Reviewer AI: review the diff and validation evidence.
- DevOps AI: inspect GitHub Actions and pipeline logs with GitHub CLI.

Use Aider for the Developer AI role when you want focused code edits.

## Team Prompt

Use this at the start of a Cline role session:

```text
You are part of my local AI software team. Current role: [role]. Follow that role only. Do not do another role's job. Do not edit files unless your role allows it. Keep scope small. Use validation evidence. Write a clear report.
```

## Safety

- Work on AI branches only.
- Do not push automatically.
- Do not edit secrets, auth, payments, deployment config, or database migrations.
- Stop after one small task.
- Prefer validation fixes before new features.
