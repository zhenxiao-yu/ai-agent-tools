param(
  [int]$IntervalSeconds = 90,
  [switch]$IncludeOptional,
  [switch]$IncludeModelDetails
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Dashboard = Join-Path $Root "dashboard"
$Venv = Join-Path $Dashboard ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
Set-Location $Root

if (-not (Test-Path -LiteralPath $Python)) {
  python -m venv $Venv
}

& $Python -m pip install -r (Join-Path $Dashboard "requirements.txt") | Out-Null

$args = @(
  "-m", "dashboard.refresh_status_snapshot",
  "--watch",
  "--interval", [string]([Math]::Max(15, $IntervalSeconds))
)

if ($IncludeOptional) {
  $args += "--include-optional"
}
if ($IncludeModelDetails) {
  $args += "--include-model-details"
}

& $Python @args
