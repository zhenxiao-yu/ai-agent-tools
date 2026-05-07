$ErrorActionPreference = "Continue"
$Root = "C:\ai-agent-tools"
$ProfilesPath = Join-Path $Root "configs\model-profiles.json"
$LogDir = Join-Path $Root "logs"

if (-not (Test-Path -LiteralPath $ProfilesPath)) {
  throw "Missing model profiles: $ProfilesPath"
}

$profiles = Get-Content -LiteralPath $ProfilesPath -Raw | ConvertFrom-Json
Write-Host "Provider Health"
Write-Host "==============="

foreach ($prop in $profiles.PSObject.Properties) {
  $p = $prop.Value
  $keyPresent = "n/a"
  if ($p.apiKeyEnvVar) {
    $keyPresent = if ([Environment]::GetEnvironmentVariable($p.apiKeyEnvVar, "Process") -or [Environment]::GetEnvironmentVariable($p.apiKeyEnvVar, "User") -or [Environment]::GetEnvironmentVariable($p.apiKeyEnvVar, "Machine")) { "yes" } else { "no" }
  }
  $lastLog = Get-ChildItem -LiteralPath $LogDir -Filter "provider-test-$($p.provider)-*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  Write-Host ""
  Write-Host "Profile: $($prop.Name)"
  Write-Host "  Provider: $($p.provider)"
  Write-Host "  Paid: $($p.paid)"
  Write-Host "  Base URL: $($p.baseUrl)"
  Write-Host "  Model: $($p.model)"
  Write-Host "  API key env var: $(if ($p.apiKeyEnvVar) { $p.apiKeyEnvVar } else { 'none' })"
  Write-Host "  Key present: $keyPresent"
  Write-Host "  Last test log: $(if ($lastLog) { $lastLog.FullName } else { 'none' })"
}
