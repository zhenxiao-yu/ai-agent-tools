<#
.SYNOPSIS
    Install whatever is missing from the local AI team toolchain.

.DESCRIPTION
    Idempotent installer. Each tool is checked first via Get-Command; if it's
    already on PATH, we skip it. Uses winget for system installs, pip for
    aider, and `code --install-extension` for Cline.

    This script does NOT pull Ollama models — that's 02-setup-models.ps1.

.PARAMETER SkipModels
    Always true here. Models are handled in the next script. Kept as a flag
    just for clarity if you read the scripts side-by-side.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\01-install-missing.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"  # don't bail on a single install failure

$ToolRoot = "C:\ai-agent-tools"
$LogDir   = Join-Path $ToolRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile   = Join-Path $LogDir "install-$Timestamp.log"
Start-Transcript -Path $LogFile -Append | Out-Null

function Section($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }

function Need-Cmd { param([string]$Name) -not (Get-Command $Name -ErrorAction SilentlyContinue) }

function Install-Winget {
    param([string]$Id)
    Write-Host "  -> winget install --id $Id" -ForegroundColor Yellow
    & winget install --id $Id -e --accept-source-agreements --accept-package-agreements
}

# ---------------------------------------------------------------------------
Section "Pre-check: winget"
if (Need-Cmd winget) {
    Write-Host "winget is not available on this machine." -ForegroundColor Red
    Write-Host "Install 'App Installer' from the Microsoft Store, then re-run this script." -ForegroundColor Red
    Stop-Transcript | Out-Null
    return
}

# ---------------------------------------------------------------------------
Section "Git"
if (Need-Cmd git)    { Install-Winget "Git.Git" }                else { Write-Host "  already installed" }

Section "VSCode"
if (Need-Cmd code)   { Install-Winget "Microsoft.VisualStudioCode" } else { Write-Host "  already installed" }

Section "Node.js LTS"
if (Need-Cmd node)   { Install-Winget "OpenJS.NodeJS.LTS" }      else { Write-Host "  already installed" }

Section "Python 3.12"
if (Need-Cmd python) { Install-Winget "Python.Python.3.12" }     else { Write-Host "  already installed" }

Section "Ollama"
if (Need-Cmd ollama) { Install-Winget "Ollama.Ollama" }          else { Write-Host "  already installed" }

Section "GitHub CLI"
if (Need-Cmd gh)     { Install-Winget "GitHub.cli" }             else { Write-Host "  already installed" }

# ---------------------------------------------------------------------------
Section "Refresh PATH for this session"
# winget puts new tools on PATH but the current shell doesn't see them until refresh.
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
            [System.Environment]::GetEnvironmentVariable("Path","User")

# ---------------------------------------------------------------------------
Section "Aider (via pip)"
if (Need-Cmd aider) {
    if (Need-Cmd python) {
        Write-Host "Python still not on PATH after install; you may need to open a new shell." -ForegroundColor Yellow
    } else {
        & python -m pip install --upgrade pip
        & python -m pip install aider-install
        & aider-install
    }
} else {
    Write-Host "  already installed"
}

# ---------------------------------------------------------------------------
Section "Cline VSCode extension"
if (Need-Cmd code) {
    Write-Host "VSCode CLI not on PATH yet; open VSCode once, then re-run this section." -ForegroundColor Yellow
} else {
    # Current working marketplace ID observed on this machine.
    & code --install-extension saoudrizwan.claude-dev
}

# ---------------------------------------------------------------------------
Section "OLLAMA_API_BASE"
$current = [System.Environment]::GetEnvironmentVariable("OLLAMA_API_BASE", "User")
if (-not $current) {
    [System.Environment]::SetEnvironmentVariable("OLLAMA_API_BASE", "http://127.0.0.1:11434", "User")
    Write-Host "  Set OLLAMA_API_BASE=http://127.0.0.1:11434 (user-level). New shells will see it."
} else {
    Write-Host "  Already set: $current"
}

# ---------------------------------------------------------------------------
Section "Done"
Write-Host "Install pass complete. Log: $LogFile"
Write-Host ""
Write-Host "IMPORTANT: open a NEW PowerShell window before continuing, so PATH refreshes." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\02-setup-models.ps1"
Write-Host "  2. powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\03-validate-setup.ps1"

Stop-Transcript | Out-Null
