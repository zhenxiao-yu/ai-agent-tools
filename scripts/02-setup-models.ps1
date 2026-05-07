<#
.SYNOPSIS
    Pull recommended local coding models via Ollama and run a quick test.

.DESCRIPTION
    Pulls qwen2.5-coder:14b as the primary. Optionally pulls
    deepseek-coder-v2:16b as the backup. Skips a model if it's already pulled.
    Then runs a tiny generation
    against the primary so you can confirm it actually works on this hardware.

.PARAMETER PullBackup
    Whether to also pull deepseek-coder-v2:16b. Default: $true.
    On limited disk, pass -PullBackup:$false.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\02-setup-models.ps1
#>

[CmdletBinding()]
param(
    [bool]$PullBackup = $false
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ToolRoot = "C:\ai-agent-tools"
$LogDir   = Join-Path $ToolRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile   = Join-Path $LogDir "models-$Timestamp.log"
Start-Transcript -Path $LogFile -Append | Out-Null

function Section($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }

# ---------------------------------------------------------------------------
Section "Verify Ollama"
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "ollama is not on PATH. Run 01-install-missing.ps1 first, then open a new shell."
}

# Make sure the API is up before trying to pull (pulls go via the daemon).
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5 | Out-Null
    Write-Host "Ollama API reachable." -ForegroundColor Green
} catch {
    Write-Host "Ollama API not responding. Starting 'ollama serve' in the background..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

# ---------------------------------------------------------------------------
function Has-Model { param([string]$Name)
    $list = & ollama list 2>$null
    return ($list -match [regex]::Escape($Name))
}

# ---------------------------------------------------------------------------
Section "Primary: qwen2.5-coder:14b"
if (Has-Model "qwen2.5-coder:14b") {
    Write-Host "  already pulled"
} else {
    & ollama pull qwen2.5-coder:14b
}

if ($PullBackup) {
    Section "Backup: deepseek-coder-v2:16b"
    if (Has-Model "deepseek-coder-v2:16b") {
        Write-Host "  already pulled"
    } else {
        & ollama pull deepseek-coder-v2:16b
    }
}
else {
    Section "Backup: deepseek-coder-v2:16b"
    Write-Host "  skipped by default. Re-run with -PullBackup `$true if you approve the extra download."
}

# ---------------------------------------------------------------------------
Section "Smoke-test the primary model"
$body = @{
    model  = "qwen2.5-coder:14b"
    prompt = "Write a TypeScript function isValidEmail(s: string): boolean. Two sentences of explanation, no markdown fences."
    stream = $false
} | ConvertTo-Json -Depth 5

$start = Get-Date
$resp  = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 300
$secs  = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)

Write-Host ""
Write-Host "--- Response ($secs s) ---"
Write-Host $resp.response

# ---------------------------------------------------------------------------
Section "Done"
Write-Host "Models log: $LogFile"
Write-Host ""
Write-Host "Next: powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\03-validate-setup.ps1" -ForegroundColor Yellow

Stop-Transcript | Out-Null
