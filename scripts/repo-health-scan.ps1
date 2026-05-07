param(
  [Parameter(Mandatory=$true)][string]$RepoPath
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$ReportDir = Join-Path $Root "reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ReportPath = Join-Path $ReportDir "repo-health-$Timestamp.md"

function Write-Step([string]$Message) { Write-Host "[repo-health] $Message" }

function Resolve-Tool([string]$Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notmatch "OpenAI\.Codex") { return $cmd.Source }
  $packageRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  if (Test-Path -LiteralPath $packageRoot) {
    $hit = Get-ChildItem -LiteralPath $packageRoot -Recurse -Filter "$Name.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($hit) { return $hit.FullName }
  }
  return $null
}

function Get-JsonFile([string]$Path) {
  try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json } catch { return $null }
}

function Guess-Framework($pkg) {
  $deps = @{}
  foreach ($section in @("dependencies","devDependencies")) {
    if ($pkg.$section) {
      $pkg.$section.PSObject.Properties | ForEach-Object { $deps[$_.Name] = $_.Value }
    }
  }
  if ($deps.ContainsKey("next")) { return "Next.js" }
  if ($deps.ContainsKey("vite")) { return "Vite" }
  if ($deps.ContainsKey("@angular/core")) { return "Angular" }
  if ($deps.ContainsKey("vue")) { return "Vue" }
  if ($deps.ContainsKey("react")) { return "React" }
  if ($deps.ContainsKey("express")) { return "Express" }
  return "Unknown web/Node project"
}

function Guess-PackageManager([string]$Path) {
  if (Test-Path (Join-Path $Path "pnpm-lock.yaml")) { return "pnpm" }
  if (Test-Path (Join-Path $Path "yarn.lock")) { return "yarn" }
  if (Test-Path (Join-Path $Path "package-lock.json")) { return "npm" }
  if (Test-Path (Join-Path $Path "bun.lockb")) { return "bun" }
  return "npm"
}

function Count-Text([string]$Path, [string]$Pattern) {
  $rg = Resolve-Tool "rg"
  if ($rg) {
    try {
      $out = & $rg --glob "!node_modules" --glob "!.git" --glob "!dist" --glob "!build" --glob "!.next" --glob "!coverage" -n $Pattern $Path 2>$null
      return @($out).Count
    } catch { return 0 }
  }
  return @(Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\(node_modules|\.git|dist|build|\.next|coverage)\\' } |
    Select-String -Pattern $Pattern -SimpleMatch -ErrorAction SilentlyContinue).Count
}

$RepoFull = (Resolve-Path -LiteralPath $RepoPath).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepoFull ".git"))) { throw "Not a Git repo: $RepoFull" }
$PackagePath = Join-Path $RepoFull "package.json"
if (-not (Test-Path -LiteralPath $PackagePath)) { throw "package.json not found: $RepoFull" }

Write-Step "Scanning $RepoFull without edits."
$pkg = Get-JsonFile $PackagePath
$scripts = @()
if ($pkg.scripts) { $scripts = $pkg.scripts.PSObject.Properties | ForEach-Object { "$($_.Name): $($_.Value)" } }
$framework = Guess-Framework $pkg
$manager = Guess-PackageManager $RepoFull

$currentBranch = (& git -C $RepoFull branch --show-current 2>$null)
$status = (& git -C $RepoFull status --porcelain 2>$null)
$dirty = if ($status) { "dirty" } else { "clean" }

$envFiles = @(Get-ChildItem -LiteralPath $RepoFull -Recurse -Force -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^\.env($|\.|.local|.development|.production|.test)' -and $_.FullName -notmatch '\\node_modules\\|\\.git\\' })

$workflowFiles = @(Get-ChildItem -LiteralPath (Join-Path $RepoFull ".github\workflows") -File -ErrorAction SilentlyContinue)
$riskyFolders = @("node_modules","dist","build",".next","coverage",".git",".turbo",".cache","Library","Temp","Logs","Obj","Builds") |
  Where-Object { Test-Path -LiteralPath (Join-Path $RepoFull $_) }
$lockfiles = @("pnpm-lock.yaml","yarn.lock","package-lock.json","bun.lockb") | Where-Object { Test-Path -LiteralPath (Join-Path $RepoFull $_) }
$eslintConfigs = @(".eslintrc",".eslintrc.json",".eslintrc.js",".eslintrc.cjs","eslint.config.js","eslint.config.mjs","eslint.config.cjs") | Where-Object { Test-Path -LiteralPath (Join-Path $RepoFull $_) }
$prettierConfigs = @(".prettierrc",".prettierrc.json",".prettierrc.js",".prettierrc.cjs","prettier.config.js","prettier.config.cjs") | Where-Object { Test-Path -LiteralPath (Join-Path $RepoFull $_) }
$playwrightConfigs = @("playwright.config.ts","playwright.config.js","playwright.config.mjs","playwright.config.cjs") | Where-Object { Test-Path -LiteralPath (Join-Path $RepoFull $_) }

$testGuess = @()
foreach ($name in @("vitest","jest","playwright","cypress","mocha","uvu")) {
  if (($pkg.dependencies.PSObject.Properties.Name + $pkg.devDependencies.PSObject.Properties.Name) -contains $name) { $testGuess += $name }
}
if (-not $testGuess) { $testGuess = @("unknown") }

$todoCount = Count-Text $RepoFull "TODO|FIXME"
$recommended = if ($scripts -match "^typecheck:") { "Run validation and fix one TypeScript error if present." }
elseif ($scripts -match "^lint:") { "Run lint and fix one lint error if present." }
elseif ($scripts -match "^build:") { "Run build and fix one build error if present." }
else { "Improve README/dev docs or add one small smoke check after manual approval." }

$report = @(
  "# Repo Health Scan"
  ""
  "Timestamp: $Timestamp"
  "Repo: $RepoFull"
  "Current branch: $currentBranch"
  "Git status: $dirty"
  ""
  "## Project"
  "- Framework guess: $framework"
  "- Package manager guess: $manager"
  "- Lockfiles: $(if ($lockfiles) { $lockfiles -join ', ' } else { 'none' })"
  "- TypeScript config: $(Test-Path (Join-Path $RepoFull 'tsconfig.json'))"
  "- ESLint config: $($eslintConfigs.Count -gt 0)"
  "- Prettier config: $($prettierConfigs.Count -gt 0)"
  "- Playwright config: $($playwrightConfigs.Count -gt 0)"
  "- Test framework guess: $($testGuess -join ', ')"
  ""
  "## Package Scripts"
  ($(if ($scripts) { $scripts | ForEach-Object { "- $_" } } else { "- none" }))
  ""
  "## Safety"
  "- TODO/FIXME count: $todoCount"
  "- .env files count: $($envFiles.Count)"
  "- GitHub workflow files: $($workflowFiles.Count)"
  "- Risky folders found: $(if ($riskyFolders) { $riskyFolders -join ', ' } else { 'none' })"
  ""
  "## Recommended First Safe Task"
  $recommended
)

$report | Set-Content -LiteralPath $ReportPath -Encoding utf8
Write-Step "Report written: $ReportPath"
Write-Host ($report -join "`n")
