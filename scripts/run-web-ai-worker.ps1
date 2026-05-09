<#
.SYNOPSIS
    Run one conservative local AI worker pass on a web repo.

.DESCRIPTION
    This script is intentionally branch-based and human-reviewed. It refuses
    dirty repos, never commits, never pushes, and writes logs/reports for each
    run. Use -DryRun before using it on a real repo.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [string]$BaseBranch = "main",

    [string]$Model = "ollama/qwen2.5-coder:14b",

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
$ReportDir = Join-Path $Root "reports"
$LockDir = Join-Path $Root "locks"
$PromptPath = Join-Path $Root "prompts\web-worker-prompt.md"
New-Item -ItemType Directory -Path $LogDir, $ReportDir, $LockDir -Force | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$RunId = "{0}-pid{1}-{2}" -f $Timestamp, $PID, (Get-Random -Minimum 1000 -Maximum 9999)
$BranchName = "ai/web-auto-$RunId"
$ModeName = if ($DryRun) { "dry-run" } else { "worker" }
$LogPath = Join-Path $LogDir "web-ai-$ModeName-$RunId.log"
$ReportPath = Join-Path $ReportDir "web-ai-$ModeName-$RunId.md"
$LockPath = $null
$LockStream = $null

function Write-Log {
    param([string]$Message)
    $Message | Tee-Object -FilePath $LogPath -Append
}

function Get-RepoLockPath {
    param([string]$Path)
    $full = ([System.IO.Path]::GetFullPath($Path)).TrimEnd('\').ToLowerInvariant()
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($full)
        $hash = ($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
        return Join-Path $LockDir "repo-$($hash.Substring(0,16)).lock"
    }
    finally {
        $sha.Dispose()
    }
}

function Enter-RepoLock {
    param([string]$Path)
    $script:LockPath = Get-RepoLockPath -Path $Path
    try {
        $script:LockStream = [System.IO.File]::Open($script:LockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $info = [System.Text.Encoding]::UTF8.GetBytes("RunId=$RunId`nPID=$PID`nRepo=$Path`nStarted=$(Get-Date -Format o)`n")
        $script:LockStream.Write($info, 0, $info.Length)
        $script:LockStream.Flush()
    }
    catch {
        throw "Another local AI worker appears to be running for this repo. Lock: $script:LockPath. If this is stale, confirm no worker is running, then delete the lock file."
    }
}

function Exit-RepoLock {
    if ($script:LockStream) {
        $script:LockStream.Dispose()
        $script:LockStream = $null
    }
    if ($script:LockPath -and (Test-Path -LiteralPath $script:LockPath)) {
        Remove-Item -LiteralPath $script:LockPath -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-LoggedNative {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [string[]]$ArgumentList = @()
    )

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $FilePath @ArgumentList 2>&1 | Tee-Object -FilePath $LogPath -Append | Out-Null
        return $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Resolve-AiderCommand {
    # Aider may be installed via aider-install into ~/.local/bin without the
    # current shell seeing it on PATH. Probe both locations.
    $cmd = Get-Command aider -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        (Join-Path $HOME ".local\bin\aider.exe"),
        (Join-Path $env:APPDATA "Python\Python312\Scripts\aider.exe"),
        (Join-Path $env:APPDATA "Python\Python312\Scripts\aider.cmd")
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Aider was not found. Expected PATH command 'aider' or $HOME\.local\bin\aider.exe."
}

function Get-PackageJson {
    return Get-Content -Raw -Path "package.json" | ConvertFrom-Json
}

function Get-PackageScripts {
    $pkg = Get-PackageJson
    if ($pkg.PSObject.Properties.Name -contains "scripts") {
        return $pkg.scripts.PSObject.Properties.Name
    }
    return @()
}

function Test-NpmScript {
    param([string]$Name)
    return ((Get-PackageScripts) -contains $Name)
}

function Get-NodeEngineWarning {
    $pkg = Get-PackageJson
    $nodeVersion = (node --version 2>$null)
    $npmVersion = (npm --version 2>$null)
    $engineNode = $null
    $engineNpm = $null

    if ($pkg.PSObject.Properties.Name -contains "engines") {
        if ($pkg.engines.PSObject.Properties.Name -contains "node") { $engineNode = $pkg.engines.node }
        if ($pkg.engines.PSObject.Properties.Name -contains "npm") { $engineNpm = $pkg.engines.npm }
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("Current Node: $nodeVersion")
    $lines.Add("Current npm: $npmVersion")

    if ($engineNode) {
        $lines.Add("package.json engines.node: $engineNode")
        $major = [int](($nodeVersion -replace '^v','').Split('.')[0])
        $simpleRequiredMajor = $null
        if ($engineNode -match '(^|[^\d])(\d{2})(\.|$)') {
            $simpleRequiredMajor = [int]$Matches[2]
        }
        if ($simpleRequiredMajor -and $engineNode -notmatch '>=' -and $major -ne $simpleRequiredMajor) {
            $lines.Add("WARNING: Current Node major $major may not match engines.node '$engineNode'. Do not auto-change Node; use nvm-windows or Volta if this repo needs another version.")
        }
        elseif ($engineNode -match '<\s*(\d{2})' -and $major -ge [int]$Matches[1]) {
            $lines.Add("WARNING: Current Node major $major appears outside engines.node '$engineNode'. Do not auto-change Node; use nvm-windows or Volta if needed.")
        }
        else {
            $lines.Add("Node engine check: no obvious conflict detected by simple checker.")
        }
    }
    else {
        $lines.Add("package.json engines.node: not specified")
    }

    if ($engineNpm) { $lines.Add("package.json engines.npm: $engineNpm") }
    return ($lines -join [Environment]::NewLine)
}

function Get-RiskyChangedFiles {
    $changed = @(git diff --name-only)
    $changed += @(git diff --name-only --cached)
    $riskyPatterns = @(
        '(^|/)\.env($|\.)',
        '(^|/)\.git/',
        '(^|/)node_modules/',
        '(^|/)dist/',
        '(^|/)build/',
        '(^|/)\.next/',
        '(^|/)coverage/',
        '(^|/)Library/',
        '(^|/)Temp/',
        '(^|/)Logs/',
        '(^|/)Obj/',
        '(^|/)Builds?/',
        '(^|/)ProjectSettings/',
        '(^|/)Assets/.+\.unity$',
        '(^|/)Assets/.+\.prefab$',
        'secret|token|credential|apikey|api-key|private-key|id_rsa|id_ed25519',
        'migration|migrations',
        'auth|payment|stripe|paypal',
        'vercel\.json|netlify\.toml|firebase\.json|wrangler\.toml|appsettings\.Production'
    )

    $risky = New-Object System.Collections.Generic.List[string]
    foreach ($file in $changed) {
        foreach ($pattern in $riskyPatterns) {
            if ($file -match $pattern) {
                $risky.Add($file)
                break
            }
        }
    }
    return @($risky | Sort-Object -Unique)
}

function Get-ValidationCommands {
    $commands = New-Object System.Collections.Generic.List[string]
    foreach ($script in @("lint", "typecheck", "build", "test", "e2e")) {
        if (Test-NpmScript $script) {
            if ($script -eq "test") {
                $pkg = Get-PackageJson
                $testCommand = $pkg.scripts.test
                if ($testCommand -match '(^|\s)vitest(\s|$)' -and $testCommand -notmatch '(^|\s)run(\s|$)') {
                    $commands.Add("npx vitest run --config vitest.config.ts")
                    continue
                }
            }
            $commands.Add("npm run $script")
        }
    }
    return @($commands)
}

function Invoke-ValidationCommand {
    param([string]$CommandText)

    if ($CommandText -eq "npx vitest run --config vitest.config.ts") {
        return Invoke-LoggedNative -FilePath "npx" -ArgumentList @("vitest", "run", "--config", "vitest.config.ts")
    }

    if ($CommandText -match '^npm run (.+)$') {
        return Invoke-LoggedNative -FilePath "npm" -ArgumentList @("run", $Matches[1])
    }

    Write-Log "Skipping unknown validation command format: $CommandText"
    return 0
}

function Write-RunReport {
    param(
        [string]$Title,
        [string]$Status,
        [string]$Branch,
        [string]$Notes
    )

    $gitStatus = (git status --short | Out-String).TrimEnd()
    $diffStat = (git diff --stat | Out-String).TrimEnd()
    $changedFiles = (git diff --name-only | Out-String).TrimEnd()
    $scripts = ((Get-PackageScripts) -join ", ")
    $nodeInfo = Get-NodeEngineWarning
    $validation = ((Get-ValidationCommands) -join [Environment]::NewLine)

    @"
# $Title

- Repo: $RepoPath
- Status: $Status
- Branch: $Branch
- Base branch: $BaseBranch
- Model: $Model
- Dry run: $DryRun
- Log: $LogPath
- Timestamp: $Timestamp
- Run ID: $RunId

## Node / npm

``````
$nodeInfo
``````

## Package Scripts

``````
$scripts
``````

## Proposed / Run Validation Commands

``````
$validation
``````

## Git Status

``````
$gitStatus
``````

## Diff Stat

``````
$diffStat
``````

## Changed Files

``````
$changedFiles
``````

## Notes

$Notes
"@ | Set-Content -Path $ReportPath -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }
if (-not $DryRun -and -not (Test-Path -LiteralPath $PromptPath)) { throw "Prompt file missing: $PromptPath" }
Enter-RepoLock -Path $RepoPath

Push-Location $RepoPath
try {
    Write-Log "# Local Web AI Worker"
    Write-Log "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'REAL ONE-TASK RUN' })"
    Write-Log "Repo: $RepoPath"
    Write-Log "BaseBranch: $BaseBranch"
    Write-Log "Model: $Model"
    Write-Log "RunId: $RunId"
    Write-Log "Planned branch: $BranchName"
    Write-Log "Log: $LogPath"
    Write-Log "Report: $ReportPath"
    Write-Log ""

    if (-not (Test-Path ".git")) { throw "Not a git repository: $RepoPath" }
    if (-not (Test-Path "package.json")) { throw "package.json not found: $RepoPath" }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git is not on PATH." }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "node is not on PATH." }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm is not on PATH." }

    Write-Log "== Node / npm =="
    Write-Log (Get-NodeEngineWarning)
    Write-Log ""

    Write-Log "== package scripts =="
    $scripts = Get-PackageScripts
    if ($scripts.Count -gt 0) { $scripts | ForEach-Object { Write-Log "  - $_" } } else { Write-Log "  none" }

    Write-Log ""
    Write-Log "== proposed validation commands =="
    $validation = Get-ValidationCommands
    if ($validation.Count -gt 0) { $validation | ForEach-Object { Write-Log "  - $_" } } else { Write-Log "  none found" }

    $dirty = git status --porcelain
    if ($dirty) {
        Write-Log ""
        Write-Log "Refusing to run: repository has uncommitted changes."
        $dirty | Tee-Object -FilePath $LogPath -Append
        Write-RunReport -Title "Web AI Worker Report" -Status "refused-dirty-repo" -Branch (git branch --show-current) -Notes "Dry run/worker refused because the repository is dirty. Commit, stash, or discard human changes first."
        throw "Refusing to run on dirty repo."
    }

    if ($DryRun) {
        Write-Log ""
        Write-Log "Dry run complete. No branch created, no dependencies installed, no Aider run, no files edited."
        Write-RunReport -Title "Web AI Worker Dry Run Report" -Status "dry-run-ok" -Branch (git branch --show-current) -Notes "Dry run only. No branch was created and no files were modified."
        Write-Host "Dry run succeeded."
        Write-Host "Log: $LogPath"
        Write-Host "Report: $ReportPath"
        exit 0
    }

    $exit = Invoke-LoggedNative -FilePath "git" -ArgumentList @("checkout", $BaseBranch)
    if ($exit -ne 0) { throw "Failed to checkout base branch: $BaseBranch" }

    $remote = git remote 2>$null | Select-Object -First 1
    if ($remote) {
        $exit = Invoke-LoggedNative -FilePath "git" -ArgumentList @("pull", "--ff-only")
        if ($exit -ne 0) { throw "Failed to pull latest with --ff-only." }
    }
    else {
        Write-Log "No git remote configured; skipping pull."
    }

    $exit = Invoke-LoggedNative -FilePath "git" -ArgumentList @("checkout", "-b", $BranchName)
    if ($exit -ne 0) { throw "Failed to create AI branch: $BranchName" }

    if (-not (Test-Path "node_modules")) {
        Write-Log "node_modules missing; running npm install."
        $exit = Invoke-LoggedNative -FilePath "npm" -ArgumentList @("install")
        if ($exit -ne 0) { throw "npm install failed." }
    }

    $Aider = Resolve-AiderCommand
    Write-Log "Using Aider: $Aider"

    $BasePrompt = Get-Content -Raw -Path $PromptPath
    $FullPrompt = @"
$BasePrompt

Additional run instructions:
- Write your final report to: $ReportPath
- Keep the change tiny.
- Do not commit.
- Do not push.
- Do not print secrets.
- Before changing files, inspect likely files and keep the edit set minimal.
- If no safe tiny task is obvious, write a report and make no changes.
- Prefer validation fixes over cosmetic edits.
- Stop after one small task.
"@

    Write-Log ""
    Write-Log "== aider run =="
    $aiderExit = Invoke-LoggedNative -FilePath $Aider -ArgumentList @("--model", $Model, "--no-auto-commits", "--yes-always", "--message", $FullPrompt)
    Write-Log "Aider exit code: $aiderExit"
    if ($aiderExit -ne 0) {
        Write-Log "Aider exited non-zero. Continuing to report current repo state."
    }

    Write-Log ""
    Write-Log "== post-checks =="
    foreach ($commandText in (Get-ValidationCommands)) {
        Write-Log "Running $commandText"
        $exit = Invoke-ValidationCommand -CommandText $commandText
        Write-Log "Exit code for ${commandText}: $exit"
    }

    $riskyChanged = @(Get-RiskyChangedFiles)
    $notes = "Review the log and diff before committing. This script does not push or commit."
    if ($riskyChanged.Count -gt 0) {
        $notes += [Environment]::NewLine + "WARNING: Risky changed files detected. Review carefully and discard unless explicitly approved:" + [Environment]::NewLine + ($riskyChanged -join [Environment]::NewLine)
        Write-Log "WARNING: Risky changed files detected:"
        $riskyChanged | ForEach-Object { Write-Log "  - $_" }
    }

    # Auto-discard the branch if the worker produced no diff at all. Saves
    # the user from running cleanup-ai-branches.ps1 against every empty run.
    $changedAfter = (git diff --name-only | Out-String).Trim()
    $stagedAfter = (git diff --cached --name-only | Out-String).Trim()
    $branchEmpty = -not ($changedAfter -or $stagedAfter)

    if ($branchEmpty) {
        Write-Log ""
        Write-Log "Worker produced no diff. Auto-discarding branch $BranchName."
        Invoke-LoggedNative -FilePath "git" -ArgumentList @("checkout", $BaseBranch) | Out-Null
        Invoke-LoggedNative -FilePath "git" -ArgumentList @("branch", "-D", $BranchName) | Out-Null
        Write-RunReport -Title "Web AI Worker Report" -Status "no-op-branch-discarded" -Branch $BaseBranch -Notes ($notes + [Environment]::NewLine + "No diff was produced; the AI branch was auto-deleted.")
        Write-Host "Branch: (auto-discarded; back on $BaseBranch)"
        Write-Host "Log: $LogPath"
        Write-Host "Report: $ReportPath"
        exit 0
    }

    Write-RunReport -Title "Web AI Worker Report" -Status "completed-review-required" -Branch $BranchName -Notes $notes

    Write-Host "Branch: $BranchName"
    Write-Host "Log: $LogPath"
    Write-Host "Report: $ReportPath"
    Write-Host "Diff summary:"
    git diff --stat
    exit 0
}
catch {
    Write-Log "ERROR: $($_.Exception.Message)"
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    Exit-RepoLock
    Pop-Location
}
