<#
.SYNOPSIS
    Read-only system inspection. Reports what's installed and what's missing.

.DESCRIPTION
    Run this FIRST, before 01-install-missing.ps1. It changes nothing — every
    command here is read-only. Output goes to console and to
    C:\ai-agent-tools\logs\inspect-<TIMESTAMP>.log.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\00-inspect-system.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
# We deliberately don't set ErrorActionPreference=Stop here — we want to
# continue past missing tools and just record them.

$ToolRoot = "C:\ai-agent-tools"
$LogDir   = Join-Path $ToolRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile   = Join-Path $LogDir "inspect-$Timestamp.log"

Start-Transcript -Path $LogFile -Append | Out-Null

function Section($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }

function Check-Cmd {
    param([string]$Name, [string]$VersionArg = "--version")
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host ("  [X] {0,-12} not on PATH" -f $Name) -ForegroundColor Red
        return $false
    }
    try {
        $v = & $Name $VersionArg 2>&1 | Select-Object -First 1
        Write-Host ("  [OK] {0,-12} {1}" -f $Name, $v) -ForegroundColor Green
    } catch {
        Write-Host ("  [OK] {0,-12} (version probe failed: {1})" -f $Name, $_.Exception.Message) -ForegroundColor Yellow
    }
    return $true
}

# ---------------------------------------------------------------------------
Section "OS / Shell"
$os = Get-CimInstance Win32_OperatingSystem
Write-Host ("  Windows:    {0} (build {1})" -f $os.Caption, $os.BuildNumber)
Write-Host ("  PowerShell: {0}" -f $PSVersionTable.PSVersion)

# ---------------------------------------------------------------------------
Section "GPU"
try {
    Get-CimInstance Win32_VideoController | ForEach-Object {
        $vramGB = if ($_.AdapterRAM) { [math]::Round($_.AdapterRAM / 1GB, 1) } else { "?" }
        Write-Host ("  - {0} (driver {1}, ~{2} GB VRAM reported)" -f $_.Name, $_.DriverVersion, $vramGB)
    }
} catch {
    Write-Host "  GPU info unavailable" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
Section "Core tools"
$git    = Check-Cmd git
$code   = Check-Cmd code
$node   = Check-Cmd node
$npm    = Check-Cmd npm
$python = Check-Cmd python
$ollama = Check-Cmd ollama
$gh     = Check-Cmd gh
$aider  = Check-Cmd aider

# ---------------------------------------------------------------------------
Section "VSCode extensions"
if ($code) {
    $exts = & code --list-extensions 2>$null
    if ($exts -match "(?i)cline") {
        Write-Host "  [OK] Cline extension installed" -ForegroundColor Green
    } else {
        Write-Host "  [X] Cline extension NOT installed" -ForegroundColor Red
    }
} else {
    Write-Host "  Skipped (VSCode CLI not on PATH)" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
Section "Playwright (per-repo only — not a global tool)"
Write-Host "  Playwright is installed per-repo with: npm install -D @playwright/test"
Write-Host "  See: C:\ai-agent-tools\configs\PLAYWRIGHT_SETUP.md"

# ---------------------------------------------------------------------------
Section "Ollama service & models"
$ollamaUp = $false
try {
    $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    $ollamaUp = $true
    Write-Host "  [OK] Ollama HTTP API is responding on 127.0.0.1:11434" -ForegroundColor Green
    if ($tags.models -and $tags.models.Count -gt 0) {
        Write-Host "  Installed models:"
        $tags.models | ForEach-Object { Write-Host ("    - {0}" -f $_.name) }
    } else {
        Write-Host "  No models installed yet. Run: ollama pull qwen2.5-coder:14b" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [X] Ollama API is NOT responding. Service may be stopped." -ForegroundColor Red
    Write-Host "      Try: ollama serve   (or restart the Ollama service)"
}

# ---------------------------------------------------------------------------
Section "GitHub CLI auth"
if ($gh) {
    & gh auth status 2>&1
} else {
    Write-Host "  Skipped (gh not on PATH)" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
Section "Quick-fire model smoke test"
if ($ollamaUp) {
    Write-Host "  Calling qwen2.5-coder:14b with a tiny prompt (timeout 60s)..."
    try {
        $body = @{ model = "qwen2.5-coder:14b"; prompt = "Reply with the single word: pong"; stream = $false } | ConvertTo-Json
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method POST -ContentType "application/json" -Body $body -TimeoutSec 60
        Write-Host ("  Response: {0}" -f $resp.response.Trim())
        Write-Host "  GPU acceleration is hard to confirm reliably here. Watch Task Manager" -ForegroundColor DarkGray
        Write-Host "  -> Performance -> GPU when this runs. AMD ROCm support on Windows is" -ForegroundColor DarkGray
        Write-Host "  partial; Ollama may fall back to CPU. Check 'ollama serve' logs." -ForegroundColor DarkGray
    } catch {
        Write-Host ("  Smoke test failed: {0}" -f $_.Exception.Message) -ForegroundColor Red
    }
} else {
    Write-Host "  Skipped (Ollama not responding)" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
Section "Summary"
Write-Host "Inspection complete. Log: $LogFile"
Write-Host ""
Write-Host "Next step:" -ForegroundColor Yellow
Write-Host "  If anything above is missing, run:"
Write-Host "    powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\01-install-missing.ps1"

Stop-Transcript | Out-Null
