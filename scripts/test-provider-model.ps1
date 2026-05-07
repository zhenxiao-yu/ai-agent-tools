param(
  [Parameter(Mandatory=$true)][string]$ProviderName,
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [Parameter(Mandatory=$true)][string]$Model,
  [Parameter(Mandatory=$true)][string]$ApiKeyEnvVar
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$SafeProvider = ($ProviderName -replace '[^A-Za-z0-9_-]', '-').ToLowerInvariant()
$LogPath = Join-Path $LogDir "provider-test-$SafeProvider-$Timestamp.log"

Write-Host "[provider-test] Provider: $ProviderName"
Write-Host "[provider-test] WARNING: this provider may be paid. One tiny request only."

$apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnvVar, "Process")
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnvVar, "User") }
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnvVar, "Machine") }
if (-not $apiKey) {
  Write-Host "[provider-test] Missing API key env var: $ApiKeyEnvVar"
  Write-Host "[provider-test] Set it with: setx $ApiKeyEnvVar `"YOUR_KEY`""
  exit 2
}

$url = $BaseUrl.TrimEnd("/") + "/chat/completions"
$body = @{
  model = $Model
  messages = @(@{ role = "user"; content = "Write a tiny TypeScript function that sums two numbers." })
  max_tokens = 120
  temperature = 0.2
} | ConvertTo-Json -Depth 6

$headers = @{
  Authorization = "Bearer $apiKey"
  "Content-Type" = "application/json"
}
if ($ProviderName -match "openrouter") {
  $headers["HTTP-Referer"] = "http://localhost"
  $headers["X-Title"] = "Local AI Agent Tools"
}

$started = Get-Date
try {
  $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body -TimeoutSec 120
  $latencyMs = [int]((Get-Date) - $started).TotalMilliseconds
  @(
    "# Provider Test"
    ""
    "Provider: $ProviderName"
    "Base URL: $BaseUrl"
    "Model: $Model"
    "Time: $Timestamp"
    "LatencyMs: $latencyMs"
    "Status: PASS"
    ""
    "## Response"
    ($response | ConvertTo-Json -Depth 10)
  ) | Set-Content -LiteralPath $LogPath -Encoding utf8
  Write-Host "[provider-test] PASS in ${latencyMs}ms"
  Write-Host "[provider-test] Log: $LogPath"
  exit 0
} catch {
  $latencyMs = [int]((Get-Date) - $started).TotalMilliseconds
  @(
    "# Provider Test"
    ""
    "Provider: $ProviderName"
    "Base URL: $BaseUrl"
    "Model: $Model"
    "Time: $Timestamp"
    "LatencyMs: $latencyMs"
    "Status: FAIL"
    ""
    "## Error"
    $_.Exception.Message
  ) | Set-Content -LiteralPath $LogPath -Encoding utf8
  Write-Host "[provider-test] FAIL"
  Write-Host "[provider-test] Log: $LogPath"
  exit 1
}
