<#
.SYNOPSIS
    Identify and (optionally) delete dead ai/web-auto-* branches from a repo.

.DESCRIPTION
    A branch is considered cleanable if any of these are true:

      - It is empty: identical to its merge-base with the base branch
        (worker ran but produced no diff)
      - It is fully merged into the base branch
      - It is older than -StaleDays days

    The current branch is never deleted. Branches with unmerged commits are
    only deleted with -Force, and the script always prints what it found
    before doing anything destructive (use -DryRun to skip the delete).

.PARAMETER RepoPath
    Path to the repo to clean. Required.

.PARAMETER BaseBranch
    Branch to compare against. Defaults to ``main``; falls back to ``master``
    if ``main`` does not exist.

.PARAMETER Pattern
    Branch glob to scan. Defaults to ``ai/web-auto-*`` because that is what
    run-web-ai-worker.ps1 produces.

.PARAMETER StaleDays
    Branches older than this with no recent commits are flagged stale. Default 14.

.PARAMETER DryRun
    Print findings but do not delete anything.

.PARAMETER Force
    Allow deleting branches with unmerged commits (uses ``git branch -D``).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [string]$BaseBranch = "main",
    [string]$Pattern = "ai/web-auto-*",
    [int]$StaleDays = 14,
    [switch]$DryRun,
    [switch]$Force
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

    # Resolve a sane base branch.
    $baseRef = $BaseBranch
    $baseExists = (git rev-parse --verify --quiet "refs/heads/$baseRef") *>&1
    if (-not $baseExists) {
        if ((git rev-parse --verify --quiet "refs/heads/master") *>&1) {
            $baseRef = "master"
            Write-Host "[cleanup] '$BaseBranch' not found; falling back to 'master'."
        }
        else {
            throw "Base branch '$BaseBranch' does not exist (and no 'master' fallback)."
        }
    }

    $current = (git rev-parse --abbrev-ref HEAD).Trim()

    $branches = @(git for-each-ref --format="%(refname:short)`t%(committerdate:iso8601)" "refs/heads/$Pattern")

    if (-not $branches -or $branches.Count -eq 0) {
        Write-Host "[cleanup] No branches matched '$Pattern'."
        exit 0
    }

    $now = Get-Date
    $candidates = New-Object System.Collections.Generic.List[object]

    foreach ($line in $branches) {
        $parts = $line -split "`t", 2
        $name = $parts[0]
        $dateText = if ($parts.Length -gt 1) { $parts[1] } else { "" }

        if ($name -eq $current) { continue }

        $reasons = New-Object System.Collections.Generic.List[string]

        # Empty? merge-base equals tip => no real commits.
        $mergeBase = (git merge-base $name $baseRef 2>$null).Trim()
        $tip = (git rev-parse $name).Trim()
        if ($mergeBase -and $mergeBase -eq $tip) {
            [void]$reasons.Add("empty")
        }

        # Fully merged into base?
        $merged = (git branch --merged $baseRef --format="%(refname:short)" |
                   ForEach-Object { $_.Trim() } |
                   Where-Object { $_ -eq $name })
        if ($merged) { [void]$reasons.Add("merged") }

        # Stale by date?
        $age = $null
        if ($dateText) {
            try {
                $age = $now - [datetime]::Parse($dateText)
                if ($age.TotalDays -ge $StaleDays) {
                    [void]$reasons.Add("stale-$([math]::Floor($age.TotalDays))d")
                }
            }
            catch { }
        }

        if ($reasons.Count -gt 0) {
            $candidates.Add([pscustomobject]@{
                Name    = $name
                Reasons = ($reasons -join ",")
                Age     = if ($age) { "$([math]::Floor($age.TotalDays))d" } else { "?" }
            })
        }
    }

    if ($candidates.Count -eq 0) {
        Write-Host "[cleanup] All $($branches.Count) matching branch(es) are healthy."
        exit 0
    }

    Write-Host ("[cleanup] {0} branch(es) eligible for cleanup:" -f $candidates.Count)
    $candidates | Sort-Object Name | Format-Table -AutoSize | Out-String | ForEach-Object { Write-Host $_ }

    if ($DryRun) {
        Write-Host "[cleanup] -DryRun specified; not deleting."
        exit 0
    }

    foreach ($entry in $candidates) {
        $reasons = $entry.Reasons
        $useForce = $Force.IsPresent -or ($reasons -match "merged|empty")

        $flag = if ($useForce) { "-D" } else { "-d" }
        Write-Host "[cleanup] git branch $flag $($entry.Name)  ($reasons)"
        $output = git branch $flag $entry.Name 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  -> kept (exit $LASTEXITCODE): $($output -join ' ')"
        }
    }

    Write-Host "[cleanup] Done."
}
finally {
    Pop-Location
}

exit 0
