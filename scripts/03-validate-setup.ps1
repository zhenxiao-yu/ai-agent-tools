<#
.SYNOPSIS
    Validate that the full local AI team setup works end-to-end.

.DESCRIPTION
    Checks tool versions, Ollama state, models, GitHub auth, scripts, and
    optionally creates a disposable test repo and dry-runs the worker against
    it. Touches NO real repos.

.PARAMETER DryRunWorker
    If $true (default), creates C:\ai-agent-tools\test-repos\web-agent-test
    and exercises run-web-ai-worker.ps1 against it. Set to $false to skip.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\03-validate-setup.ps1
#>

[CmdletBinding()]
param(
    [bool]$DryRunWorker = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$ToolRoot = "C:\ai-agent-tools"
$LogDir   = Join-Path $ToolRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile   = Join-Path $LogDir "validate-$Timestamp.log"
Start-Transcript -Path $LogFile -Append | Out-Null

function Section($t) { Write-Host ""; Write-Host "=== $t ===" -ForegroundColor Cyan }

# ---------------------------------------------------------------------------
Section "Tool versions"
foreach ($pair in @(
    @{ n = "git";    a = "--version" },
    @{ n = "code";   a = "--version" },
    @{ n = "node";   a = "--version" },
    @{ n = "npm";    a = "--version" },
    @{ n = "python"; a = "--version" },
    @{ n = "ollama"; a = "--version" },
    @{ n = "gh";     a = "--version" },
    @{ n = "aider";  a = "--version" }
)) {
    if (Get-Command $pair.n -ErrorAction SilentlyContinue) {
        $v = (& $pair.n $pair.a 2>&1 | Select-Object -First 1)
        Write-Host ("  [OK] {0,-8} {1}" -f $pair.n, $v) -ForegroundColor Green
    } else {
        Write-Host ("  [X]  {0,-8} not on PATH" -f $pair.n) -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
Section "Ollama models"
try {
    $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    $tags.models | ForEach-Object { Write-Host ("  - {0}" -f $_.name) }
    if (-not ($tags.models.name -contains "qwen2.5-coder:14b")) {
        Write-Host "  [WARN] qwen2.5-coder:14b not present. Run 02-setup-models.ps1." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [X] Ollama API unreachable" -ForegroundColor Red
}

# ---------------------------------------------------------------------------
Section "Cline VSCode extension"
if (Get-Command code -ErrorAction SilentlyContinue) {
    $exts = & code --list-extensions 2>$null
    if ($exts -match "(?i)cline") {
        Write-Host "  [OK] Cline installed" -ForegroundColor Green
    } else {
        Write-Host "  [X] Cline not installed. Run: code --install-extension cline.cline" -ForegroundColor Red
    }
}

# ---------------------------------------------------------------------------
Section "GitHub CLI auth"
if (Get-Command gh -ErrorAction SilentlyContinue) {
    & gh auth status 2>&1
} else {
    Write-Host "  [X] gh not installed" -ForegroundColor Red
}

# ---------------------------------------------------------------------------
Section "Scripts present"
$expected = @(
    "scripts\00-inspect-system.ps1",
    "scripts\01-install-missing.ps1",
    "scripts\02-setup-models.ps1",
    "scripts\03-validate-setup.ps1",
    "scripts\run-web-ai-worker.ps1",
    "scripts\audit-web-repo.ps1",
    "scripts\morning-review.ps1",
    "scripts\check-github-pipelines.ps1",
    "scripts\run-ai-reviewer.ps1",
    "scripts\test-local-model.ps1",
    "scripts\install-scheduled-web-worker.ps1",
    "scripts\remove-scheduled-web-worker.ps1",
    "prompts\web-worker-prompt.md",
    "tasks\web-app-tasks.md",
    "configs\AGENTS.web.template.md",
    "configs\PLAYWRIGHT_SETUP.md",
    "configs\CLINE_LOCAL_SETUP.md",
    "configs\AIDER_LOCAL_SETUP.md",
    "configs\FIRST_REAL_REPO_CHECKLIST.md",
    "configs\repo-allowlist.txt",
    "team\prompts\01-product-manager.md",
    "team\prompts\02-tech-lead.md",
    "team\prompts\03-developer.md",
    "team\prompts\04-qa.md",
    "team\prompts\05-reviewer.md",
    "team\prompts\06-devops.md",
    "README.md"
)
$missing = @()
foreach ($rel in $expected) {
    $p = Join-Path $ToolRoot $rel
    if (Test-Path $p) {
        Write-Host ("  [OK] {0}" -f $rel) -ForegroundColor Green
    } else {
        Write-Host ("  [X]  {0}" -f $rel) -ForegroundColor Red
        $missing += $rel
    }
}

# ---------------------------------------------------------------------------
if ($DryRunWorker) {
    Section "Disposable test repo setup"

    $testRoot = Join-Path $ToolRoot "test-repos"
    $testRepo = Join-Path $testRoot "web-agent-test"

    if (-not (Test-Path $testRoot)) { New-Item -ItemType Directory -Path $testRoot -Force | Out-Null }
    if (-not (Test-Path $testRepo)) { New-Item -ItemType Directory -Path $testRepo -Force | Out-Null }

    Set-Location $testRepo

    if (-not (Test-Path (Join-Path $testRepo ".git"))) {
        & git init -b main | Out-Null
        & git config user.email "ai-team@local"
        & git config user.name  "AI Team"
        @{
            name        = "web-agent-test"
            version     = "0.0.1"
            scripts     = @{
                lint      = "echo lint-ok"
                typecheck = "echo typecheck-ok"
                build     = "echo build-ok"
                test      = "echo test-ok"
            }
        } | ConvertTo-Json -Depth 5 | Out-File -FilePath (Join-Path $testRepo "package.json") -Encoding UTF8
        "# test repo`n" | Out-File -FilePath (Join-Path $testRepo "README.md") -Encoding UTF8
        & git add .
        & git commit -m "init" | Out-Null
    }

    Write-Host "Test repo ready at: $testRepo" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can dry-run the worker now (no edits):" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File $ToolRoot\scripts\run-web-ai-worker.ps1 -RepoPath `"$testRepo`" -BaseBranch main -DryRun"
    Write-Host ""
    Write-Host "(Skipping auto-execution to keep this validation step itself read-mostly.)"
}

# ---------------------------------------------------------------------------
Section "Summary"
if ($missing.Count -eq 0) {
    Write-Host "All expected files are present." -ForegroundColor Green
} else {
    Write-Host "Missing files:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" }
}
Write-Host ""
Write-Host "Validation log: $LogFile"

Stop-Transcript | Out-Null
