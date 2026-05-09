<#
.SYNOPSIS
    One-shot end-to-end run: clone (if needed) -> init agents -> dry-run ->
    worker -> reviewer -> branch cleanup. Designed so a daily user types one
    repo path or URL and walks away.

.DESCRIPTION
    Stages, in order:

      1. Resolve target. If -RemoteUrl is supplied (or -Target looks like a
         URL), clone into C:\ai-agent-tools\workspaces\<owner>-<name> when
         that local path does not already exist. Otherwise treat -Target as
         an absolute path that already contains a git repo.
      2. Init agents config (AGENTS.md + .ai-agent-tools/web-worker.md) if
         missing, by calling init-repo-agents.ps1.
      3. Dry-run worker (run-web-ai-worker.ps1 -DryRun). Stops on failure
         unless -SkipDryRun is set.
      4. Worker pass (run-web-ai-worker.ps1).
      5. Reviewer pass against the worker's branch (or current branch if
         the worker auto-discarded an empty branch).
      6. cleanup-ai-branches.ps1 against the repo to drop other empty/merged
         branches that may have piled up.

    Each stage's output streams into the parent's stdout, so when this script
    is run under the dashboard async-job wrapper, the Runs page shows the
    combined log. Failure of an early stage skips later stages but always
    runs the cleanup pass at the end.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [string]$RemoteUrl = "",
    [string]$BaseBranch = "main",
    [string]$Model = "ollama/qwen2.5-coder:14b",
    [switch]$SkipDryRun,
    [switch]$SkipReviewer,
    [switch]$SkipCleanup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = "C:\ai-agent-tools"
$Scripts = Join-Path $Root "scripts"
$WorkspaceRoot = Join-Path $Root "workspaces"
New-Item -ItemType Directory -Path $WorkspaceRoot -Force | Out-Null

function Section([string]$Name) {
    Write-Host ""
    Write-Host "===== $Name ====="
}

function Slug([string]$Text) {
    $clean = -join ($Text.ToCharArray() | ForEach-Object {
        if ($_ -match '[A-Za-z0-9._-]') { $_ } else { '-' }
    })
    return $clean.Trim('-')
}

# ---------- resolve target ----------
Section "Resolving target"

# Accept Target as either local path or URL. RemoteUrl takes precedence if set.
$looksLikeUrl = ($Target -match '^(https?://|git@)') -or ($RemoteUrl)
$LocalPath = $Target
$CloneUrl = $RemoteUrl

if ($looksLikeUrl) {
    if (-not $CloneUrl) { $CloneUrl = $Target }

    # Parse owner/name out of the URL.
    $owner = "unknown"
    $name = "repo"
    if ($CloneUrl -match '^https?://[^/]+/([^/]+)/([^/?#]+?)(?:\.git)?(?:[/?#].*)?$') {
        $owner = $Matches[1]; $name = $Matches[2]
    }
    elseif ($CloneUrl -match '^git@[^:]+:([^/]+)/([^/]+?)(?:\.git)?$') {
        $owner = $Matches[1]; $name = $Matches[2]
    }

    $folder = "{0}-{1}" -f (Slug $owner), (Slug $name)
    $LocalPath = Join-Path $WorkspaceRoot $folder
    Write-Host "Remote URL : $CloneUrl"
    Write-Host "Local path : $LocalPath"

    if (Test-Path -LiteralPath (Join-Path $LocalPath ".git")) {
        Write-Host "Workspace already present; pulling base branch updates."
        Push-Location $LocalPath
        try {
            git fetch --all --prune *>&1 | Out-Host
            $defaultRemote = (git remote 2>$null | Select-Object -First 1)
            if ($defaultRemote) {
                # Best-effort sync of the configured base branch; do not abort if it fails.
                git checkout $BaseBranch *>&1 | Out-Host
                git pull --ff-only *>&1 | Out-Host
            }
        }
        finally { Pop-Location }
    }
    else {
        Write-Host "Cloning ..."
        git clone --depth 50 $CloneUrl $LocalPath *>&1 | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "git clone failed for $CloneUrl" }
    }
}
else {
    if (-not (Test-Path -LiteralPath $LocalPath)) { throw "Target path does not exist: $LocalPath" }
    if (-not (Test-Path -LiteralPath (Join-Path $LocalPath ".git"))) { throw "Target is not a git repository: $LocalPath" }
    Write-Host "Local path : $LocalPath"
}

# Resolve the actual default branch on the fresh clone if the caller's BaseBranch is wrong.
Push-Location $LocalPath
try {
    $exists = git rev-parse --verify --quiet "refs/heads/$BaseBranch" *>&1
    if (-not $exists) {
        foreach ($candidate in @("main", "master", "develop", "trunk")) {
            $check = git rev-parse --verify --quiet "refs/heads/$candidate" *>&1
            if ($check) {
                Write-Host "Base branch '$BaseBranch' missing; using '$candidate'."
                $BaseBranch = $candidate
                break
            }
        }
    }
}
finally { Pop-Location }

# ---------- init agents ----------
Section "Init agents config"
& (Join-Path $Scripts "init-repo-agents.ps1") -RepoPath $LocalPath
if ($LASTEXITCODE -ne 0) { throw "init-repo-agents failed (exit $LASTEXITCODE)" }

# ---------- dry-run ----------
$dryRunOk = $true
if (-not $SkipDryRun) {
    Section "Dry-run"
    & (Join-Path $Scripts "run-web-ai-worker.ps1") -RepoPath $LocalPath -BaseBranch $BaseBranch -Model $Model -DryRun
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[magic] Dry-run failed (exit $LASTEXITCODE); skipping worker and reviewer."
        $dryRunOk = $false
    }
}

# ---------- worker ----------
$workerOk = $false
if ($dryRunOk) {
    Section "Worker"
    & (Join-Path $Scripts "run-web-ai-worker.ps1") -RepoPath $LocalPath -BaseBranch $BaseBranch -Model $Model
    $workerOk = ($LASTEXITCODE -eq 0)
    if (-not $workerOk) { Write-Host "[magic] Worker exited $LASTEXITCODE; skipping reviewer." }
}

# ---------- reviewer ----------
if ($workerOk -and -not $SkipReviewer) {
    Section "Reviewer"
    & (Join-Path $Scripts "run-ai-reviewer.ps1") -RepoPath $LocalPath
    if ($LASTEXITCODE -ne 0) { Write-Host "[magic] Reviewer exited $LASTEXITCODE." }
}

# ---------- cleanup ----------
if (-not $SkipCleanup) {
    Section "Branch cleanup"
    & (Join-Path $Scripts "cleanup-ai-branches.ps1") -RepoPath $LocalPath -BaseBranch $BaseBranch
}

Section "Done"
Write-Host "Repo : $LocalPath"
Write-Host "Base : $BaseBranch"
exit 0
