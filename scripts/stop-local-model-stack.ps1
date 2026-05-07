$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
$PidPath = Join-Path $LogDir "free-claude-code-proxy.pid"

function Write-Step([string]$Message) { Write-Host "[local-ai-stack] $Message" }

if (-not (Test-Path -LiteralPath $PidPath)) {
  Write-Step "No proxy PID file found. Nothing started by these scripts is known to be running."
  exit 0
}

$pidText = (Get-Content -LiteralPath $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
if (-not $pidText -or -not ($pidText -match '^\d+$')) {
  Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
  throw "Proxy PID file was invalid and has been removed."
}

$proc = Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue
if (-not $proc) {
  Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
  Write-Step "Recorded proxy process is no longer running."
  exit 0
}

$cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
if ($cmdLine -notmatch "free-claude-code" -and $cmdLine -notmatch "uvicorn") {
  throw "Refusing to stop PID $($proc.Id) because it does not look like the local free-claude-code proxy."
}

Write-Step "Stopping proxy process PID $($proc.Id)."
Stop-Process -Id $proc.Id -Force
Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
Write-Step "Stopped proxy started by local scripts. Ollama was left running."
