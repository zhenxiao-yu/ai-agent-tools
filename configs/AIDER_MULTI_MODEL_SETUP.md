# Aider Multi-Model Setup

## Local Default

```powershell
aider --model ollama/qwen2.5-coder:14b
```

This is the default for local branch worker tasks.

## Paid Provider Pattern

Use environment variables for keys. Avoid putting API keys directly in commands because terminal history can persist.

Examples:

```powershell
setx DEEPSEEK_API_KEY "YOUR_KEY"
```

Then use Aider's OpenAI-compatible/provider syntax where supported by your installed Aider version. Keep paid use manual and supervised.

## Safety

- Do not use paid models for scheduled 24/7 work by default.
- Do not push automatically.
- Do not commit automatically.
- Use AI branches only.
- Run validation and review before committing.
- Use local Ollama fallback when a key is missing or cost is unclear.
