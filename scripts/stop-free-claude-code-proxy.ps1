<#
.SYNOPSIS
    Stop the free-claude-code (Claude-compatible) local proxy.

.DESCRIPTION
    Reads logs/free-claude-code-proxy.pid (written by the start script) and
    stops the recorded process. Falls back to the listener on the configured
    port if the PID file is missing or stale. Safe to call when nothing is
    running.
#>

[CmdletBinding()]
param(
  [int]$Port = 8082
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
$PidPath = Join-Path $LogDir "free-claude-code-proxy.pid"

function Write-Step([string]$Message) { Write-Host "[free-claude-code] $Message" }

$stoppedAny = $false

if (Test-Path -LiteralPath $PidPath) {
    $pidValue = (Get-Content -LiteralPath $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($pidValue) {
        try {
            $proc = Get-Process -Id ([int]$pidValue) -ErrorAction Stop
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            Write-Step "Stopped recorded proxy process (PID $($proc.Id))."
            $stoppedAny = $true
        }
        catch {
            Write-Step "Recorded PID $pidValue is not running. Cleaning up stale PID file."
        }
    }
    Remove-Item -LiteralPath $PidPath -Force -ErrorAction SilentlyContinue
}

# Fallback: stop whatever owns the port
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $listener) {
    try {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction Stop
        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
        Write-Step "Stopped process holding port ${Port}: $($proc.ProcessName) (PID $($proc.Id))."
        $stoppedAny = $true
    }
    catch {
        # Skip processes we cannot inspect/stop.
    }
}

if (-not $stoppedAny) {
    Write-Step "Proxy was not running."
}

exit 0
