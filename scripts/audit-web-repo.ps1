<#
.SYNOPSIS
    No-edit audit for a web repository before running local AI workers.

.DESCRIPTION
    Reads repo metadata, package scripts, risky paths, branch/dirty state, and
    writes a report. It never creates branches, installs dependencies, edits
    files, commits, or pushes.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = "C:\ai-agent-tools"
$ReportDir = Join-Path $Root "reports"
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportPath = Join-Path $ReportDir "repo-audit-$Timestamp.md"

function Get-FrameworkGuess {
    param($Package)
    $deps = @{}
    foreach ($section in @("dependencies", "devDependencies")) {
        if ($Package.PSObject.Properties.Name -contains $section) {
            foreach ($p in $Package.$section.PSObject.Properties) {
                $deps[$p.Name] = $p.Value
            }
        }
    }

    $scriptsText = ""
    if ($Package.PSObject.Properties.Name -contains "scripts") {
        $scriptsText = (($Package.scripts.PSObject.Properties | ForEach-Object { $_.Value }) -join " ")
    }

    $guesses = New-Object System.Collections.Generic.List[string]
    if ($deps.ContainsKey("next") -or $scriptsText -match "\bnext\b") { $guesses.Add("Next.js") }
    if ($deps.ContainsKey("vite") -or $scriptsText -match "\bvite\b") { $guesses.Add("Vite") }
    if ($deps.ContainsKey("react")) { $guesses.Add("React") }
    if ($deps.ContainsKey("vue")) { $guesses.Add("Vue") }
    if ($deps.ContainsKey("express")) { $guesses.Add("Express") }
    if ($deps.ContainsKey("tailwindcss")) { $guesses.Add("Tailwind CSS") }
    if ($deps.ContainsKey("@playwright/test")) { $guesses.Add("Playwright") }

    if ($guesses.Count -eq 0) { return "Unknown JavaScript/Node web project" }
    return (($guesses | Select-Object -Unique) -join ", ")
}

function Get-RiskyPaths {
    $patterns = @(
        ".env", ".env.local", ".env.production", ".npmrc", ".yarnrc.yml",
        "vercel.json", "netlify.toml", "firebase.json", "wrangler.toml",
        "migrations", "prisma\migrations", "supabase\migrations",
        "node_modules", "dist", "build", ".next", "coverage",
        "Library", "Temp", "Logs", "Obj", "Build", "Builds", "ProjectSettings"
    )

    $found = New-Object System.Collections.Generic.List[string]
    foreach ($pattern in $patterns) {
        Get-ChildItem -LiteralPath . -Force -Recurse -Depth 3 -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -notmatch '\\\.git(\\|$)' -and $_.Name -ieq (Split-Path $pattern -Leaf) } |
            ForEach-Object { $found.Add((Resolve-Path -LiteralPath $_.FullName -Relative)) }
    }
    return @($found | Sort-Object -Unique)
}

function Get-RecommendedTask {
    param($Scripts, [bool]$IsDirty)
    if ($IsDirty) { return "Do not run AI yet. Commit, stash, or discard human changes first." }
    if ($Scripts -contains "build") { return "Run a dry-run, then let the worker inspect and fix at most one build/type/lint issue." }
    if ($Scripts -contains "typecheck") { return "Run a dry-run, then prefer one TypeScript/typecheck fix." }
    if ($Scripts -contains "lint") { return "Run a dry-run, then prefer one lint fix." }
    if ($Scripts -contains "test") { return "Run a dry-run, then prefer one failing test fix or one small smoke test." }
    return "Start with README/dev setup documentation or add one safe validation script."
}

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }

Push-Location $RepoPath
try {
    if (-not (Test-Path ".git")) { throw "Not a git repository: $RepoPath" }
    if (-not (Test-Path "package.json")) { throw "package.json not found: $RepoPath" }

    $pkg = Get-Content -Raw -Path "package.json" | ConvertFrom-Json
    $branch = (git branch --show-current)
    $status = (git status --short | Out-String).TrimEnd()
    $isDirty = -not [string]::IsNullOrWhiteSpace($status)
    $scripts = @()
    if ($pkg.PSObject.Properties.Name -contains "scripts") { $scripts = @($pkg.scripts.PSObject.Properties.Name) }
    $scriptLines = if ($pkg.PSObject.Properties.Name -contains "scripts") { ($pkg.scripts.PSObject.Properties | ForEach-Object { "$($_.Name): $($_.Value)" }) -join [Environment]::NewLine } else { "none" }
    $framework = Get-FrameworkGuess -Package $pkg
    $risky = @(Get-RiskyPaths)
    $riskyText = if ($risky.Count -gt 0) { $risky -join [Environment]::NewLine } else { "No common risky paths found in shallow scan." }
    $nodeVersion = (node --version 2>$null)
    $npmVersion = (npm --version 2>$null)
    $engines = if ($pkg.PSObject.Properties.Name -contains "engines") { ($pkg.engines | ConvertTo-Json -Depth 5) } else { "not specified" }
    $recommended = Get-RecommendedTask -Scripts $scripts -IsDirty $isDirty

    @"
# Web Repo Audit

- Repo: $RepoPath
- Timestamp: $Timestamp
- Current branch: $branch
- Dirty: $isDirty
- Framework guess: $framework
- Node: $nodeVersion
- npm: $npmVersion

## package.json engines

``````
$engines
``````

## Package Scripts

``````
$scriptLines
``````

## Git Status

``````
$status
``````

## Risky Files / Folders Found

``````
$riskyText
``````

## Recommended First Safe AI Task

$recommended

## Next Safe Command

``````powershell
powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\run-web-ai-worker.ps1 -RepoPath "$RepoPath" -BaseBranch "$branch" -DryRun
``````
"@ | Set-Content -Path $ReportPath -Encoding UTF8

    Write-Host "Repo: $RepoPath"
    Write-Host "Branch: $branch"
    Write-Host "Dirty: $isDirty"
    Write-Host "Framework guess: $framework"
    Write-Host "Package scripts:"
    if ($scriptLines) { Write-Host $scriptLines } else { Write-Host "none" }
    Write-Host "Risky files/folders found:"
    Write-Host $riskyText
    Write-Host "Recommended first safe AI task: $recommended"
    Write-Host "Audit report: $ReportPath"
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
finally {
    Pop-Location
}
