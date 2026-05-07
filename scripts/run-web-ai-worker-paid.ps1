param(
  [Parameter(Mandatory=$true)][string]$RepoPath,
  [string]$BaseBranch = "main",
  [Parameter(Mandatory=$true)][string]$ProviderName,
  [Parameter(Mandatory=$true)][string]$BaseUrl,
  [Parameter(Mandatory=$true)][string]$Model,
  [Parameter(Mandatory=$true)][string]$ApiKeyEnvVar
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
$ReportDir = Join-Path $Root "reports"
$PromptPath = Join-Path $Root "prompts\web-worker-prompt.md"
New-Item -ItemType Directory -Force -Path $LogDir,$ReportDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BranchName = "ai/paid-web-auto-$Timestamp"
$LogPath = Join-Path $LogDir "paid-web-ai-worker-$Timestamp.log"
$ReportPath = Join-Path $ReportDir "paid-web-ai-worker-$Timestamp.md"
$PromptRunPath = Join-Path $LogDir "paid-web-ai-worker-prompt-$Timestamp.md"

function Write-Step([string]$Message) {
  Write-Host "[paid-worker] $Message"
  Add-Content -LiteralPath $LogPath -Value "[paid-worker] $Message"
}

function Resolve-Aider {
  $cmd = Get-Command aider -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $candidate = Join-Path $env:USERPROFILE ".local\bin\aider.exe"
  if (Test-Path -LiteralPath $candidate) { return $candidate }
  throw "Aider was not found."
}

Set-Content -LiteralPath $LogPath -Encoding utf8 -Value "Paid worker run $Timestamp"
Write-Step "WARNING: this is manual paid turbo mode and may use paid tokens."
Write-Step "Provider: $ProviderName"
Write-Step "Base URL: $BaseUrl"
Write-Step "Model: $Model"

$apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnvVar, "Process")
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnvVar, "User") }
if (-not $apiKey) { $apiKey = [Environment]::GetEnvironmentVariable($ApiKeyEnvVar, "Machine") }
if (-not $apiKey) {
  throw "Missing API key env var $ApiKeyEnvVar. Set it with: setx $ApiKeyEnvVar `"YOUR_KEY`""
}

$RepoFull = (Resolve-Path -LiteralPath $RepoPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepoFull ".git"))) { throw "Not a Git repo: $RepoFull" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoFull "package.json"))) { throw "package.json not found: $RepoFull" }
$dirty = git -C $RepoFull status --porcelain
if ($dirty) {
  Write-Step "Refusing dirty repo:"
  $dirty | ForEach-Object { Add-Content -LiteralPath $LogPath -Value $_ }
  throw "Refusing to run on dirty repo."
}

Write-Step "Checking out base branch $BaseBranch."
git -C $RepoFull checkout $BaseBranch *>> $LogPath
if ($LASTEXITCODE -ne 0) { throw "Failed to checkout $BaseBranch" }
git -C $RepoFull pull --ff-only *>> $LogPath
if ($LASTEXITCODE -ne 0) { throw "Failed to pull $BaseBranch with --ff-only" }
git -C $RepoFull checkout -b $BranchName *>> $LogPath
if ($LASTEXITCODE -ne 0) { throw "Failed to create branch $BranchName" }

$pkg = Get-Content -LiteralPath (Join-Path $RepoFull "package.json") -Raw | ConvertFrom-Json
$scripts = @{}
if ($pkg.scripts) { $pkg.scripts.PSObject.Properties | ForEach-Object { $scripts[$_.Name] = $_.Value } }

if (-not (Test-Path -LiteralPath (Join-Path $RepoFull "node_modules"))) {
  Write-Step "node_modules missing. Paid worker will not install dependencies automatically; run repo validation manually after dependencies are ready."
}

$aider = Resolve-Aider
$prompt = @"
Manual paid turbo mode. This may cost money.

Use provider: $ProviderName
Report path: $ReportPath

Follow the local web worker rules below. Make exactly one small safe change only.
Do not touch secrets, .env files, auth, payments, database migrations, deployment config, generated files, node_modules, build outputs, or binary artifacts.
Do not commit. Do not push. Stop after one small task and write a report.

$(Get-Content -LiteralPath $PromptPath -Raw)
"@
$prompt | Set-Content -LiteralPath $PromptRunPath -Encoding utf8

Write-Step "Running Aider once on paid OpenAI-compatible endpoint."
Push-Location $RepoFull
try {
  $env:AIDER_OPENAI_API_KEY = $apiKey
  $env:AIDER_OPENAI_API_BASE = $BaseUrl
  & $aider --model "openai/$Model" --openai-api-base $BaseUrl --no-auto-commits --message-file $PromptRunPath *>> $LogPath
} finally {
  Remove-Item Env:\AIDER_OPENAI_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:\AIDER_OPENAI_API_BASE -ErrorAction SilentlyContinue
  Pop-Location
}

foreach ($scriptName in @("lint","typecheck","build","test","e2e")) {
  if ($scripts.ContainsKey($scriptName)) {
    Write-Step "Running npm run $scriptName"
    cmd /c "npm run $scriptName" *>> $LogPath
  }
}

$status = git -C $RepoFull status --short
$diffStat = git -C $RepoFull diff --stat
@(
  "# Paid Web AI Worker"
  ""
  "Timestamp: $Timestamp"
  "Repo: $RepoFull"
  "Branch: $BranchName"
  "Provider: $ProviderName"
  "Model: $Model"
  "Paid: true"
  "Log: $LogPath"
  ""
  "## Status"
  "````text"
  ($status -join "`n")
  "````"
  ""
  "## Diff Stat"
  "````text"
  ($diffStat -join "`n")
  "````"
  ""
  "No commit or push was performed."
) | Set-Content -LiteralPath $ReportPath -Encoding utf8

Write-Step "Branch: $BranchName"
Write-Step "Log: $LogPath"
Write-Step "Report: $ReportPath"
Write-Step "No commit or push was performed."
