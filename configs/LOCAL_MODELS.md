# Local Models

This machine uses Ollama for always-free local model runs.

## Installed Models

- `qwen2.5-coder:14b`: default coding model. Best current choice for web-app edits, small TypeScript fixes, focused reviews, and Aider/Cline local work.
- `llama3.2:3b`: fast tiny model if installed. Good for smoke tests, short summaries, and checking that the stack is alive. It is not the main coding model.

## Optional Models

- `deepseek-coder-v2:16b`: optional backup coding model. Pull only when you approve the disk/time cost.
- Larger Qwen coder models: optional planning/review models only if performance is acceptable on the RX 7900 XT and available RAM.

## Recommended Routing

- Default coding: `qwen2.5-coder:14b`
- Fast health checks: `llama3.2:3b`
- Backup coding: `deepseek-coder-v2:16b`

## Commands

List models:

```powershell
ollama list
```

Pull a model:

```powershell
ollama pull qwen2.5-coder:14b
```

Remove a model:

```powershell
ollama rm MODEL_NAME
```

Larger models use more disk, RAM, and VRAM. Do not pull large models during an active work session unless you are ready to wait.
