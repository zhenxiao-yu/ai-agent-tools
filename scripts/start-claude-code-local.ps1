param(
  [int]$Port = 8082
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"

Write-Host "[claude-local] Starting/checking local model stack."
& (Join-Path $Root "scripts\start-free-claude-code-proxy.ps1") -Port $Port

$claude = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claude) {
  Write-Host "[claude-local] Claude Code CLI was not found on PATH."
  Write-Host "[claude-local] Proxy is ready at http://127.0.0.1:$Port for compatible VS Code extensions or a future Claude Code CLI install."
  exit 2
}

Write-Host "[claude-local] Launching Claude Code CLI with session-scoped local proxy settings."
$env:ANTHROPIC_AUTH_TOKEN = "freecc"
$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:$Port"
$env:CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY = "1"
& $claude.Source
