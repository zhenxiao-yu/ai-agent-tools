$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$ReportsDir = Join-Path $Root "reports"
$TempRoot = Join-Path $env:TEMP ("ai-agent-diagnostics-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ZipPath = Join-Path $ReportsDir "diagnostic-bundle-$Timestamp.zip"
New-Item -ItemType Directory -Force -Path $ReportsDir,$TempRoot | Out-Null

function Write-SafeFile([string]$Name, [scriptblock]$Block) {
  $path = Join-Path $TempRoot $Name
  try {
    & $Block 2>&1 |
      ForEach-Object { $_ -replace '(gho_[A-Za-z0-9_\-]+|sk-[A-Za-z0-9_\-]+)', '********' } |
      Set-Content -LiteralPath $path -Encoding utf8
  } catch {
    "Failed: $($_.Exception.Message)" | Set-Content -LiteralPath $path -Encoding utf8
  }
}

Write-SafeFile "ai-stack-monitor.txt" { powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\ai-stack-monitor.ps1") }
Write-SafeFile "provider-health.txt" { powershell -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\provider-health.ps1") }
Write-SafeFile "scheduled-tasks.txt" { Get-ScheduledTask -TaskName "Local Web AI Worker","Local Ollama Auto Start","Local Free Claude Code Proxy Auto Start" -ErrorAction SilentlyContinue | Format-List *; Get-ScheduledTaskInfo -TaskName "Local Web AI Worker" -ErrorAction SilentlyContinue | Format-List * }
Write-SafeFile "versions.txt" {
  code --version
  git --version
  node --version
  npm --version
  pnpm --version
  python --version
  ollama --version
  gh --version
}

$latestDir = Join-Path $TempRoot "latest"
New-Item -ItemType Directory -Force -Path $latestDir | Out-Null
foreach ($folderName in @("logs","reports","team\reports")) {
  $source = Join-Path $Root $folderName
  if (-not (Test-Path -LiteralPath $source)) { continue }
  $dest = Join-Path $latestDir ($folderName -replace '\\','-')
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  Get-ChildItem -LiteralPath $source -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch '\.env|secret|credential|api-key|key' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 12 |
    ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $dest $_.Name) -Force }
}

Compress-Archive -Path (Join-Path $TempRoot "*") -DestinationPath $ZipPath -Force
Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Diagnostic bundle created: $ZipPath"
