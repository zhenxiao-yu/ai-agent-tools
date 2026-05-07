param(
  [switch]$IncludePaid
)

$ErrorActionPreference = "Continue"
$Root = "C:\ai-agent-tools"
$ReportDir = Join-Path $Root "reports"
$ProfilesPath = Join-Path $Root "configs\model-profiles.json"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportPath = Join-Path $ReportDir "model-comparison-$Timestamp.md"
$Prompt = "Write a tiny TypeScript function that sums two numbers."
$results = @()

function Add-Result($Provider, $Model, $Success, $LatencyMs, $Note, $Paid) {
  $script:results += [pscustomobject]@{
    Provider = $Provider
    Model = $Model
    Success = $Success
    LatencyMs = $LatencyMs
    Note = $Note
    Paid = $Paid
  }
}

$started = Get-Date
try {
  $body = @{ model = "qwen2.5-coder:14b"; prompt = $Prompt; stream = $false; options = @{ num_predict = 120 } } | ConvertTo-Json -Depth 6
  $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
  Add-Result "ollama" "qwen2.5-coder:14b" "pass" ([int]((Get-Date)-$started).TotalMilliseconds) "local free baseline; response length $($resp.response.Length)" $false
} catch {
  Add-Result "ollama" "qwen2.5-coder:14b" "fail" ([int]((Get-Date)-$started).TotalMilliseconds) $_.Exception.Message $false
}

$profiles = Get-Content -LiteralPath $ProfilesPath -Raw | ConvertFrom-Json
foreach ($prop in $profiles.PSObject.Properties) {
  $p = $prop.Value
  if (-not $p.paid -or -not $p.apiKeyEnvVar) { continue }
  if (-not $IncludePaid) {
    Add-Result $p.provider $p.model "skipped" 0 "paid test skipped; rerun with -IncludePaid for one tiny paid request" $true
    continue
  }
  $apiKey = [Environment]::GetEnvironmentVariable($p.apiKeyEnvVar, "Process")
  if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($p.apiKeyEnvVar, "User") }
  if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($p.apiKeyEnvVar, "Machine") }
  if (-not $apiKey) {
    Add-Result $p.provider $p.model "skipped" 0 "missing $($p.apiKeyEnvVar); paid test not run" $true
    continue
  }
  $started = Get-Date
  try {
    $headers = @{ Authorization = "Bearer $apiKey"; "Content-Type" = "application/json" }
    if ($p.provider -eq "openrouter") {
      $headers["HTTP-Referer"] = "http://localhost"
      $headers["X-Title"] = "Local AI Agent Tools"
    }
    $body = @{ model = $p.model; messages = @(@{ role = "user"; content = $Prompt }); max_tokens = 120; temperature = 0.2 } | ConvertTo-Json -Depth 6
    $resp = Invoke-RestMethod -Uri ($p.baseUrl.TrimEnd("/") + "/chat/completions") -Method Post -Headers $headers -Body $body -TimeoutSec 120
    Add-Result $p.provider $p.model "pass" ([int]((Get-Date)-$started).TotalMilliseconds) "tiny paid request succeeded" $true
  } catch {
    Add-Result $p.provider $p.model "fail" ([int]((Get-Date)-$started).TotalMilliseconds) $_.Exception.Message $true
  }
}

$lines = @(
  "# Model Comparison"
  ""
  "Timestamp: $Timestamp"
  "Prompt: $Prompt"
  ""
  "| Provider | Model | Success | Latency ms | Paid | Note |"
  "|---|---|---:|---:|---:|---|"
)
foreach ($r in $results) {
  $note = ($r.Note -replace '\|','/' -replace "`r?`n",' ')
  $lines += "| $($r.Provider) | $($r.Model) | $($r.Success) | $($r.LatencyMs) | $($r.Paid) | $note |"
}
$lines | Set-Content -LiteralPath $ReportPath -Encoding utf8
Write-Host "Comparison report: $ReportPath"
$lines -join "`n"
