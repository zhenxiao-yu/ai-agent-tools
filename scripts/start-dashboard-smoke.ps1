param(
  [int]$Port = 8512
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Dashboard = Join-Path $Root "dashboard"
$Venv = Join-Path $Dashboard ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
  python -m venv $Venv
}

& $Python -m pip install -r (Join-Path $Dashboard "requirements.txt") | Out-Null

Set-Location $Dashboard
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
& $Python -m streamlit run (Join-Path $Dashboard "app.py") --server.address 127.0.0.1 --server.port $Port --server.headless true --browser.gatherUsageStats false
