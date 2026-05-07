param(
  [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Dashboard = Join-Path $Root "dashboard"
$Venv = Join-Path $Dashboard ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "dashboard-start.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Step([string]$Message) {
  Write-Host "[dashboard] $Message"
  Add-Content -LiteralPath $LogPath -Value "[$(Get-Date -Format s)] $Message"
}

function Test-Dashboard {
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -TimeoutSec 3 -UseBasicParsing | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (Test-Dashboard) {
  Write-Step "Dashboard already running at http://127.0.0.1:$Port"
  try { Start-Process "http://127.0.0.1:$Port" | Out-Null } catch { Write-Step "Browser auto-open failed; open the URL manually." }
  exit 0
}

Write-Host "[dashboard] Preparing local Streamlit environment."
if (-not (Test-Path -LiteralPath $Python)) {
  Write-Step "Creating local Python venv: $Venv"
  python -m venv $Venv
}

try {
  Write-Step "Installing/updating Streamlit requirements."
  & $Python -m pip install --upgrade pip *> $LogPath
  & $Python -m pip install -r (Join-Path $Dashboard "requirements.txt") *>> $LogPath
} catch {
  Write-Step "Failed to install Streamlit requirements. See $LogPath"
  throw
}

Write-Step "Starting at http://127.0.0.1:$Port"
Write-Step "Log: $LogPath"
try { Start-Process "http://127.0.0.1:$Port" | Out-Null } catch { Write-Step "Browser auto-open failed; open the URL manually." }
Set-Location $Dashboard
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
& $Python -m streamlit run (Join-Path $Dashboard "app.py") --server.address 127.0.0.1 --server.port $Port --server.headless true --browser.gatherUsageStats false
