# Provider Keys Setup

Local Ollama remains the default. Paid providers are optional turbo mode and should not be scheduled 24/7 without explicit budget controls.

## Providers To Sign Up For

- DeepSeek: create `DEEPSEEK_API_KEY`
- Qwen / Alibaba Model Studio: create `QWEN_API_KEY`
- Kimi / Moonshot: create `KIMI_API_KEY`
- SiliconFlow: create `SILICONFLOW_API_KEY`
- OpenRouter: create `OPENROUTER_API_KEY`
- Z.ai / GLM: create `ZAI_API_KEY`

## Set Keys

```powershell
setx DEEPSEEK_API_KEY "YOUR_KEY"
setx QWEN_API_KEY "YOUR_KEY"
setx KIMI_API_KEY "YOUR_KEY"
setx SILICONFLOW_API_KEY "YOUR_KEY"
setx OPENROUTER_API_KEY "YOUR_KEY"
setx ZAI_API_KEY "YOUR_KEY"
```

Open a new terminal after `setx`.

## Verify Without Printing Keys

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\provider-health.ps1
```

Secrets helper:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\manage-provider-secrets.ps1 -Action List
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\manage-provider-secrets.ps1 -Action Set -Provider deepseek
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\manage-provider-secrets.ps1 -Action Remove -Provider deepseek
```

The helper never prints key values. It stores keys in your user-level Windows environment variables.

Run one tiny paid test only after you understand the cost:

```powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\test-provider-model.ps1 -ProviderName deepseek -BaseUrl "https://api.deepseek.com" -Model "deepseek-chat" -ApiKeyEnvVar DEEPSEEK_API_KEY
```

## Rotate Or Delete Keys

Rotate keys in the provider console first, then update your local environment variable with `setx`.

To remove a user-level key:

```powershell
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", $null, "User")
```

Repeat for the specific provider key.

## Avoid Committing Secrets

- Never put real keys in repos.
- Never paste keys into prompts.
- Never create `.env` files inside project repos unless you are deliberately configuring that repo.
- Keep templates only under `C:\ai-agent-tools\configs\providers`.
- Use local Ollama when a paid key is missing or budget is unclear.

## Local Fallback

```powershell
aider --model ollama/qwen2.5-coder:14b
```

## Scheduling Warning

Do not schedule paid models for 24/7 work by default. Use local Ollama for scheduled maintenance. Paid providers are for manual supervised turbo runs only.
