<#
.SYNOPSIS
    Run the full advisory team-prompt pipeline against a repo.

.DESCRIPTION
    Executes the six role prompts in team/prompts/ in sequence:
        01 Product Manager  -> picks one small task
        02 Tech Lead        -> turns the task into an execution plan
        03 Developer        -> describes the implementation path
        04 QA               -> runs/recommends validation and reports outcomes
        05 Reviewer         -> reviews the current diff (if any)
        06 DevOps           -> reviews CI/devops signals via gh CLI when available

    Every role calls the local Ollama model with its role prompt plus a curated
    repo-context block (git status, diff, package.json scripts, latest worker
    log, gh run list when available). Prior role output is forwarded to later
    roles so the chain stays coherent. The combined report is written to
    team/reports/pipeline-<timestamp>.md.

    The pipeline never edits files. To act on a task it surfaces, run the worker.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [string]$Model = "qwen2.5-coder:14b",

    [string[]]$Roles = @("pm", "tl", "dev", "qa", "review", "devops"),

    [int]$TimeoutSec = 600
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = "C:\ai-agent-tools"
$PromptDir = Join-Path $Root "team\prompts"
$ReportDir = Join-Path $Root "team\reports"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Path $ReportDir, $LogDir -Force | Out-Null

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportPath = Join-Path $ReportDir "pipeline-$Timestamp.md"

# Map short role keys to prompt files + display labels.
$RoleMap = [ordered]@{
    pm     = @{ File = "01-product-manager.md"; Label = "Product Manager" }
    tl     = @{ File = "02-tech-lead.md";       Label = "Tech Lead" }
    dev    = @{ File = "03-developer.md";       Label = "Developer (advisory)" }
    qa     = @{ File = "04-qa.md";              Label = "QA" }
    review = @{ File = "05-reviewer.md";        Label = "Reviewer" }
    devops = @{ File = "06-devops.md";          Label = "DevOps" }
}

function Invoke-Ollama {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Prompt
    )

    $body = @{
        model  = $Model
        prompt = $Prompt
        stream = $false
    } | ConvertTo-Json -Depth 5 -Compress

    try {
        $response = Invoke-RestMethod `
            -Uri "http://127.0.0.1:11434/api/generate" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -TimeoutSec $TimeoutSec
        return [string]$response.response
    }
    catch {
        return "ERROR: model call failed: $($_.Exception.Message)"
    }
}

function Get-RepoContext {
    Push-Location $RepoPath
    try {
        if (-not (Test-Path ".git")) { throw "Not a git repository: $RepoPath" }

        $status = (git status --short | Out-String).TrimEnd()
        $branch = (git rev-parse --abbrev-ref HEAD 2>$null | Out-String).Trim()
        $diffStat = (git diff --stat | Out-String).TrimEnd()
        $diff = (git diff --no-ext-diff | Out-String).TrimEnd()
        if ($diff.Length -gt 8000) { $diff = $diff.Substring(0, 8000) + "`n... (diff truncated)" }

        $packageScripts = ""
        if (Test-Path "package.json") {
            try {
                $pkg = Get-Content -Raw -Path "package.json" | ConvertFrom-Json
                if ($pkg.PSObject.Properties.Name -contains "scripts") {
                    $packageScripts = ($pkg.scripts.PSObject.Properties.Name -join ", ")
                }
            }
            catch { $packageScripts = "(unable to parse package.json)" }
        }

        $readmeHead = ""
        foreach ($candidate in @("README.md", "readme.md", "README")) {
            if (Test-Path $candidate) {
                $readmeHead = (Get-Content -Path $candidate -TotalCount 60 | Out-String).TrimEnd()
                break
            }
        }

        $latestWorkerLog = Get-ChildItem (Join-Path $Root "logs") -Include "web-ai-worker-*.log" -File -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        $workerSummary = if ($latestWorkerLog) {
            $tail = (Get-Content -Path $latestWorkerLog.FullName -Tail 80 | Out-String).TrimEnd()
            "$($latestWorkerLog.Name)`n$tail"
        }
        else { "No recent worker log." }

        $ghOutput = "(gh CLI not available)"
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            try {
                $ghOutput = (gh run list --limit 5 2>$null | Out-String).TrimEnd()
                if (-not $ghOutput) { $ghOutput = "(no recent gh runs)" }
            }
            catch { $ghOutput = "(gh run list failed)" }
        }

        return [pscustomobject]@{
            Branch         = $branch
            Status         = if ($status) { $status } else { "(clean)" }
            DiffStat       = if ($diffStat) { $diffStat } else { "(no staged or unstaged diff)" }
            Diff           = if ($diff) { $diff } else { "(no diff)" }
            PackageScripts = if ($packageScripts) { $packageScripts } else { "(none detected)" }
            ReadmeHead     = if ($readmeHead) { $readmeHead } else { "(no README found)" }
            WorkerSummary  = $workerSummary
            GhRuns         = $ghOutput
        }
    }
    finally {
        Pop-Location
    }
}

function Build-RolePrompt {
    param(
        [string]$Instructions,
        [pscustomobject]$Context,
        [hashtable]$PriorOutputs
    )

    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine($Instructions.TrimEnd())
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("=== Repository Context ===")
    [void]$sb.AppendLine("Path: $RepoPath")
    [void]$sb.AppendLine("Branch: $($Context.Branch)")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Git status:")
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine($Context.Status)
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Diff stat:")
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine($Context.DiffStat)
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Diff (truncated):")
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine($Context.Diff)
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Package scripts: $($Context.PackageScripts)")
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("README head:")
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine($Context.ReadmeHead)
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Latest worker log tail:")
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine($Context.WorkerSummary)
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine()
    [void]$sb.AppendLine("Recent gh runs:")
    [void]$sb.AppendLine('```')
    [void]$sb.AppendLine($Context.GhRuns)
    [void]$sb.AppendLine('```')

    if ($PriorOutputs.Count -gt 0) {
        [void]$sb.AppendLine()
        [void]$sb.AppendLine("=== Prior Role Outputs ===")
        foreach ($key in $PriorOutputs.Keys) {
            [void]$sb.AppendLine()
            [void]$sb.AppendLine("--- $($RoleMap[$key].Label) ---")
            [void]$sb.AppendLine($PriorOutputs[$key])
        }
    }

    return $sb.ToString()
}

# Sanity-check role list before doing any work.
$normalizedRoles = @()
foreach ($role in $Roles) {
    $key = $role.ToLowerInvariant()
    if (-not $RoleMap.Contains($key)) { throw "Unknown role: $role" }
    $normalizedRoles += $key
}

$context = Get-RepoContext
$priorOutputs = [ordered]@{}

$report = New-Object System.Text.StringBuilder
[void]$report.AppendLine("# Agent Pipeline Report")
[void]$report.AppendLine()
[void]$report.AppendLine("- Repo: $RepoPath")
[void]$report.AppendLine("- Branch: $($context.Branch)")
[void]$report.AppendLine("- Model: $Model")
[void]$report.AppendLine("- Timestamp: $Timestamp")
[void]$report.AppendLine("- Roles: $($normalizedRoles -join ' -> ')")
[void]$report.AppendLine()
[void]$report.AppendLine("> The pipeline produces advisory output only. No files are edited.")
[void]$report.AppendLine()

foreach ($role in $normalizedRoles) {
    $entry = $RoleMap[$role]
    $promptFile = Join-Path $PromptDir $entry.File
    if (-not (Test-Path -LiteralPath $promptFile)) {
        Write-Host "Skipping $role (prompt file missing: $promptFile)"
        continue
    }
    $instructions = (Get-Content -Raw -Path $promptFile).TrimEnd()

    Write-Host "[$role] $($entry.Label) thinking..."
    $prompt = Build-RolePrompt -Instructions $instructions -Context $context -PriorOutputs $priorOutputs
    $output = Invoke-Ollama -Prompt $prompt
    $priorOutputs[$role] = $output

    [void]$report.AppendLine("## $($entry.Label)")
    [void]$report.AppendLine()
    [void]$report.AppendLine($output.TrimEnd())
    [void]$report.AppendLine()
}

[void]$report.AppendLine("---")
[void]$report.AppendLine()
[void]$report.AppendLine("Generated by run-agent-pipeline.ps1")

$report.ToString() | Set-Content -Path $ReportPath -Encoding UTF8

Write-Host ""
Write-Host "Pipeline report: $ReportPath"
exit 0
