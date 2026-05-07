param(
  [Parameter(Mandatory=$true)][string]$RepoPath
)

$ErrorActionPreference = "Continue"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
$ReportDir = Join-Path $Root "reports"
New-Item -ItemType Directory -Force -Path $LogDir,$ReportDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogDir "repo-validation-$Timestamp.log"
$ReportPath = Join-Path $ReportDir "repo-validation-$Timestamp.md"

function Write-Step([string]$Message) {
  Write-Host "[repo-validation] $Message"
  Add-Content -LiteralPath $LogPath -Value "[repo-validation] $Message"
}

function Get-PackageManager([string]$Path) {
  if (Test-Path (Join-Path $Path "pnpm-lock.yaml")) { return "pnpm" }
  if (Test-Path (Join-Path $Path "yarn.lock")) { return "yarn" }
  if (Test-Path (Join-Path $Path "package-lock.json")) { return "npm" }
  return "npm"
}

function Run-Cmd([string]$Command) {
  Write-Step "Running: $Command"
  Add-Content -LiteralPath $LogPath -Value "`n> $Command"
  Push-Location $RepoFull
  try {
    cmd /c $Command *>> $LogPath
    $code = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  Write-Step "Exit code: $code"
  return $code
}

$RepoFull = (Resolve-Path -LiteralPath $RepoPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepoFull ".git"))) { throw "Not a Git repo: $RepoFull" }
$PackagePath = Join-Path $RepoFull "package.json"
if (-not (Test-Path -LiteralPath $PackagePath)) { throw "package.json not found: $RepoFull" }

Set-Content -LiteralPath $LogPath -Encoding utf8 -Value "Repo validation run $Timestamp`nRepo: $RepoFull`n"
$pkg = Get-Content -LiteralPath $PackagePath -Raw | ConvertFrom-Json
$scripts = @{}
if ($pkg.scripts) { $pkg.scripts.PSObject.Properties | ForEach-Object { $scripts[$_.Name] = $_.Value } }
$pm = Get-PackageManager $RepoFull

Write-Step "Repo: $RepoFull"
Write-Step "Package manager: $pm"
Write-Step "Node: $(node --version 2>$null)"
Write-Step "npm: $(npm --version 2>$null)"
if (Get-Command pnpm -ErrorAction SilentlyContinue) { Write-Step "pnpm: $(pnpm --version 2>$null)" }
if (Get-Command yarn -ErrorAction SilentlyContinue) { Write-Step "yarn: $(yarn --version 2>$null)" }

$results = @()
foreach ($scriptName in @("lint","typecheck","build","test","e2e")) {
  if ($scripts.ContainsKey($scriptName)) {
    $cmd = "$pm run $scriptName"
    $code = Run-Cmd $cmd
    $results += [pscustomobject]@{ Script=$scriptName; Command=$cmd; ExitCode=$code }
  } else {
    Write-Step "Skipping missing script: $scriptName"
    $results += [pscustomobject]@{ Script=$scriptName; Command="missing"; ExitCode="skipped" }
  }
}

$report = @(
  "# Repo Validation"
  ""
  "Timestamp: $Timestamp"
  "Repo: $RepoFull"
  "Package manager: $pm"
  "Log: $LogPath"
  ""
  "## Results"
)
foreach ($r in $results) { $report += "- $($r.Script): $($r.ExitCode) ($($r.Command))" }
$report | Set-Content -LiteralPath $ReportPath -Encoding utf8
Write-Step "Report written: $ReportPath"
if (($results | Where-Object { $_.ExitCode -is [int] -and $_.ExitCode -ne 0 })) { exit 1 }
exit 0
