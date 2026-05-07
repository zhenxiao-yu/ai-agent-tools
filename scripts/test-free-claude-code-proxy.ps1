param(
  [int]$Port = 8082
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogDir "free-claude-code-test-$Timestamp.log"

function Write-Step([string]$Message) { Write-Host "[free-claude-code-test] $Message" }

Write-Step "Checking Ollama API."
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5 | Out-Null

Write-Step "Checking proxy models endpoint."
$models = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/models" -Headers @{ "x-api-key" = "freecc" } -TimeoutSec 10

Write-Step "Sending tiny Anthropic-compatible message through local proxy."
$body = @{
  model = "claude-3-5-haiku-latest"
  max_tokens = 64
  messages = @(@{ role = "user"; content = "Reply with exactly: local-proxy-ok" })
} | ConvertTo-Json -Depth 5

$headers = @{
  "x-api-key" = "freecc"
  "anthropic-version" = "2023-06-01"
}

$response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/messages" -Method Post -Headers $headers -ContentType "application/json" -Body $body -TimeoutSec 180

@(
  "# free-claude-code proxy test"
  ""
  "Timestamp: $Timestamp"
  "Proxy: http://127.0.0.1:$Port"
  "Models endpoint: OK"
  ""
  "## Models"
  ($models | ConvertTo-Json -Depth 8)
  ""
  "## Response"
  ($response | ConvertTo-Json -Depth 8)
) | Set-Content -LiteralPath $LogPath -Encoding utf8

Write-Step "PASS. Test log: $LogPath"
