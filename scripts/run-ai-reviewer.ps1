param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [string]$Model = "qwen2.5-coder:14b"
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}
$Root = "C:\ai-agent-tools"
$ReportDir = Join-Path $Root "team\reports"
New-Item -ItemType Directory -Path $ReportDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportPath = Join-Path $ReportDir "review-$Timestamp.md"

if (-not (Test-Path -LiteralPath $RepoPath)) {
    throw "RepoPath does not exist: $RepoPath"
}

Push-Location $RepoPath
try {
    if (-not (Test-Path ".git")) { throw "Not a git repository: $RepoPath" }

    $Status = (git status --short | Out-String).TrimEnd()
    $DiffStat = (git diff --stat | Out-String).TrimEnd()
    $Diff = (git diff --no-ext-diff | Out-String).TrimEnd()
    $RecentValidation = Get-ChildItem "C:\ai-agent-tools\logs" -Include "web-ai-worker-*.log","manual-validation-*.log" -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    $ValidationText = if ($RecentValidation) {
        Get-Content -Raw -Path $RecentValidation.FullName
    }
    else {
        "No recent worker validation log found."
    }

    if (-not $Diff) {
        @"
# AI Review

- Repo: $RepoPath
- Timestamp: $Timestamp
- Model: $Model

## Approval Status

request changes

## Reason

No git diff was found. There is nothing to review.

## Git Status

``````
$Status
``````
"@ | Set-Content -Path $ReportPath -Encoding UTF8
        Write-Host "Reviewer report: $ReportPath"
        return
    }

    $Prompt = @"
You are the Senior Code Reviewer AI.

Do not edit files.

Review this git diff and validation evidence.

Return:
- approval status: approve / request changes / reject
- risks
- required fixes
- files changed
- validation status
- suggested commit message

Reject or request changes if risky files were touched, scope is too large, validation failed without explanation, or the diff does not solve a small useful task.

Important validation rule:
- Test stderr warnings are not failures by themselves.
- Treat validation as passing when the command exit code is 0 and the summary says tests passed.

Git status:
``````
$Status
``````

Diff stat:
``````
$DiffStat
``````

Diff:
``````
$Diff
``````

Recent validation log:
``````
$ValidationText
``````
"@

    $Body = @{
        model  = $Model
        prompt = $Prompt
        stream = $false
    } | ConvertTo-Json -Depth 5

    $Response = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -ContentType "application/json" -Body $Body -TimeoutSec 900

    @"
# AI Review

- Repo: $RepoPath
- Timestamp: $Timestamp
- Model: $Model

## Git Status

``````
$Status
``````

## Diff Stat

``````
$DiffStat
``````

## Review

$($Response.response)
"@ | Set-Content -Path $ReportPath -Encoding UTF8

    Write-Host "Reviewer report: $ReportPath"
}
finally {
    Pop-Location
}
