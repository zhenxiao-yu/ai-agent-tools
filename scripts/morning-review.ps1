<#
.SYNOPSIS
    Human morning review helper for AI-created branches and reports.

.DESCRIPTION
    Shows branch, status, recent AI branches, latest logs/reports, and diff
    summary. It never commits, pushes, discards, or edits files. Add
    -RunReviewer to request a local-model review of the current diff.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [switch]$RunReviewer
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }

Push-Location $RepoPath
try {
    if (-not (Test-Path ".git")) { throw "Not a git repository: $RepoPath" }

    Write-Host "== Repo =="
    Write-Host $RepoPath

    Write-Host ""
    Write-Host "== Current branch =="
    git branch --show-current

    Write-Host ""
    Write-Host "== Git status =="
    git status --short

    Write-Host ""
    Write-Host "== Recent AI branches =="
    git branch --sort=-committerdate --list "ai/*" | Select-Object -First 10

    Write-Host ""
    Write-Host "== Diff stat =="
    git diff --stat

    Write-Host ""
    Write-Host "== Latest worker reports =="
    Get-ChildItem "C:\ai-agent-tools\reports" -Filter "*.md" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 8 FullName, LastWriteTime |
        Format-Table -AutoSize

    Write-Host ""
    Write-Host "== Latest logs =="
    Get-ChildItem "C:\ai-agent-tools\logs" -Filter "*.log" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 8 FullName, LastWriteTime |
        Format-Table -AutoSize

    if ($RunReviewer) {
        Write-Host ""
        Write-Host "== Running reviewer =="
        powershell -ExecutionPolicy Bypass -File "C:\ai-agent-tools\scripts\run-ai-reviewer.ps1" -RepoPath $RepoPath
    }
    else {
        Write-Host ""
        Write-Host "Reviewer not run. Add -RunReviewer to run it."
    }

    Write-Host ""
    Write-Host "No commit, push, discard, or file edit was performed."
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    Pop-Location
}
