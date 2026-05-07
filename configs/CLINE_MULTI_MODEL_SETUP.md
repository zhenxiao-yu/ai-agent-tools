# Cline Multi-Model Setup

## Local Ollama Mode

- Provider: `Ollama`
- Base URL: `http://localhost:11434`
- Model: `qwen2.5-coder:14b`

Use this as the default.

## OpenAI-Compatible Paid Mode

- Provider: `OpenAI Compatible`
- Base URL: provider base URL
- API key: provider key
- Model: provider model

Provider examples:

- DeepSeek: `https://api.deepseek.com`, `deepseek-chat`
- Qwen / Alibaba Model Studio: `https://dashscope.aliyuncs.com/compatible-mode/v1`, `qwen-plus`
- Kimi / Moonshot: `https://api.moonshot.ai/v1`, `kimi-k2-0905-preview`
- SiliconFlow: `https://api.siliconflow.cn/v1`
- OpenRouter: `https://openrouter.ai/api/v1`
- Z.ai / GLM: verify your account endpoint; common GLM OpenAI-compatible endpoint is `https://open.bigmodel.cn/api/paas/v4`

## Recommended Routing

- Docs/comments: local Ollama
- Lint/typecheck/build fixes: local first, DeepSeek/Qwen if stuck
- UI component polish: local or Qwen
- Long repo analysis: Kimi/Qwen/DeepSeek long-context
- Review: Qwen/GLM/Kimi
- Overnight scheduled mode: local only
- Auth/payment/database/deployment: human-supervised only

Paid providers may cost money. Do not schedule them by default.
