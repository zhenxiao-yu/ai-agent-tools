param(
  [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $Root "scripts\start-dashboard.ps1"
$Url = "http://127.0.0.1:$Port"

function Test-Dashboard {
  try {
    Invoke-WebRequest -Uri $Url -TimeoutSec 3 -UseBasicParsing | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (Test-Dashboard) {
  Write-Host "[dashboard] Dashboard already running at $Url"
  Start-Process $Url | Out-Null
  exit 0
}

Write-Host "[dashboard] Dashboard is not running. Starting it now."
& $StartScript -Port $Port
