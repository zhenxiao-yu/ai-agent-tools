<#
.SYNOPSIS
    Install the optional scheduled local AI worker for one explicitly allowed repo.

.DESCRIPTION
    Scheduled mode is off by default. This installer refuses to create a task
    unless the exact repo path is present in C:\ai-agent-tools\configs\repo-allowlist.txt.
    It schedules one worker pass per interval; no loop, commit, or push.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [string]$BaseBranch = "main",

    [int]$IntervalHours = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$TaskName = "Local Web AI Worker"
$ScriptPath = "C:\ai-agent-tools\scripts\run-web-ai-worker.ps1"
$AllowlistPath = "C:\ai-agent-tools\configs\repo-allowlist.txt"

function Get-NormalizedPath {
    param([string]$Path)
    return ([System.IO.Path]::GetFullPath($Path)).TrimEnd('\')
}

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }
if (-not (Test-Path -LiteralPath $ScriptPath)) { throw "Worker script missing: $ScriptPath" }
if (-not (Test-Path -LiteralPath $AllowlistPath)) { throw "Allowlist missing: $AllowlistPath" }
if ($IntervalHours -lt 1) { throw "IntervalHours must be at least 1." }
if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) { throw "RepoPath is not a git repository: $RepoPath" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoPath "package.json"))) { throw "RepoPath does not contain package.json: $RepoPath" }

$normalizedRepo = Get-NormalizedPath $RepoPath
$allowed = Get-Content -Path $AllowlistPath |
    ForEach-Object { $_.Trim() } |
    Where-Object { $_ -and -not $_.StartsWith("#") } |
    ForEach-Object { Get-NormalizedPath $_ }

if ($allowed -notcontains $normalizedRepo) {
    throw "Refusing scheduled setup. Add the exact repo path to $AllowlistPath first: $normalizedRepo"
}

$Pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $Pwsh) { $Pwsh = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" }

$Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -RepoPath `"$normalizedRepo`" -BaseBranch `"$BaseBranch`""
$Action = New-ScheduledTaskAction -Execute $Pwsh -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours $IntervalHours) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -AllowStartIfOnBatteries:$false -DisallowStartIfOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Runs one safe local AI web worker pass per interval. No push, no auto-commit." -Force | Out-Null

Write-Host "Scheduled task installed: $TaskName"
Write-Host "Repo: $normalizedRepo"
Write-Host "Runs every $IntervalHours hour(s), one small branch-based worker pass per run."
Write-Host "No broad repo scanning is configured."
Write-Host "Disable/remove with:"
Write-Host "powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\remove-scheduled-web-worker.ps1"
