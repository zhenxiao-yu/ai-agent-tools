param(
  [string]$Model = "qwen2.5-coder:14b",
  [int]$Port = 8082
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$Project = Join-Path $Root "free-claude-code"
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "free-claude-code-proxy.log"
$PidPath = Join-Path $LogDir "free-claude-code-proxy.pid"
$EnvPath = Join-Path $Project ".env"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Step([string]$Message) { Write-Host "[free-claude-code] $Message" }

function Test-Proxy([string]$Uri) {
  try {
    Invoke-RestMethod -Uri $Uri -Headers @{ "x-api-key" = "freecc" } -TimeoutSec 3 -ErrorAction Stop | Out-Null
    return $true
  } catch {
    return $false
  }
}

if (-not (Test-Path -LiteralPath $Project)) { throw "free-claude-code folder not found: $Project" }
if (-not (Test-Path -LiteralPath $EnvPath)) { throw "Missing local proxy config: $EnvPath" }

Write-Step "Checking Ollama."
& (Join-Path $Root "scripts\start-local-model-stack.ps1") -SkipProxyTest | Out-Null

$models = (ollama list 2>$null) -join "`n"
if ($models -notmatch [regex]::Escape($Model)) {
  throw "Required Ollama model '$Model' is not installed. Run: ollama pull $Model"
}

if (Test-Proxy "http://127.0.0.1:$Port/v1/models") {
  Write-Step "Proxy is already responding at http://127.0.0.1:$Port"
  exit 0
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
  throw "Port $Port is already in use, but the proxy did not respond. Check the owning process before continuing."
}

$uv = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uv) { throw "uv was not found. It is required by free-claude-code." }

Write-Step "Starting proxy on http://127.0.0.1:$Port with model $Model."
$pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }

$safeProject = $Project.Replace("'", "''")
$safeEnv = $EnvPath.Replace("'", "''")
$safeLog = $LogPath.Replace("'", "''")
$safeUv = $uv.Replace("'", "''")
$cmd = "`$env:FCC_ENV_FILE='$safeEnv'; Set-Location '$safeProject'; &'$safeUv' run uvicorn server:app --host 127.0.0.1 --port $Port *>> '$safeLog'"
$proc = Start-Process -FilePath $pwsh -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-Command",$cmd) -WindowStyle Hidden -PassThru
$proc.Id | Set-Content -LiteralPath $PidPath -Encoding ascii

for ($i = 1; $i -le 45; $i++) {
  Start-Sleep -Seconds 1
  if (Test-Proxy "http://127.0.0.1:$Port/v1/models") {
    Write-Step "Proxy is responding at http://127.0.0.1:$Port"
    Write-Step "Log: $LogPath"
    exit 0
  }
}

Write-Error "Proxy did not respond after startup. See $LogPath"
exit 1
