$ErrorActionPreference = "Continue"
$Root = "C:\ai-agent-tools"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Report = Join-Path $Root "reports\doctor-$Timestamp.md"
New-Item -ItemType Directory -Force -Path (Split-Path $Report -Parent) | Out-Null

function Test-Http([string]$Uri, [hashtable]$Headers = @{}) {
  try {
    Invoke-RestMethod -Uri $Uri -Headers $Headers -TimeoutSec 5 -ErrorAction Stop | Out-Null
    return "PASS"
  } catch {
    return "FAIL: $($_.Exception.Message)"
  }
}

function Tool-Version([string]$Name, [string[]]$ToolArgs = @("--version")) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  if (-not $cmd) { return "MISSING" }
  try {
    $output = & $cmd.Source @ToolArgs 2>&1
    $first = $output | Where-Object { $_ } | Select-Object -First 1
    if ($first) { return $first.ToString() }
    return "FOUND: $($cmd.Source)"
  } catch {
    return "FOUND: $($cmd.Source)"
  }
}

$null = gh auth status 2>$null
$GhAuth = if ($LASTEXITCODE -eq 0) { "PASS" } else { "NOT LOGGED IN OR FAILED" }

$lines = @(
  "# Local AI Doctor"
  ""
  "Timestamp: $Timestamp"
  ""
  "## Core"
  "- C:\\ai-agent-tools exists: $(Test-Path $Root)"
  "- Dashboard HTTP: $(Test-Http 'http://127.0.0.1:8501')"
  "- Ollama API: $(Test-Http 'http://127.0.0.1:11434/api/tags')"
  "- free-claude-code proxy: $(Test-Http 'http://127.0.0.1:8082/v1/models' @{ 'x-api-key'='freecc' })"
  ""
  "## Tools"
  "- VS Code: $(Tool-Version 'code' @('--version'))"
  "- Git: $(Tool-Version 'git' @('--version'))"
  "- Node: $(Tool-Version 'node' @('--version'))"
  "- npm: $(Tool-Version 'npm' @('--version'))"
  "- pnpm: $(Tool-Version 'pnpm' @('--version'))"
  "- Python: $(Tool-Version 'python' @('--version'))"
  "- Aider: $(if ((Get-Command aider -ErrorAction SilentlyContinue) -or (Test-Path \"$env:USERPROFILE\.local\bin\aider.exe\")) { 'installed' } else { 'missing' })"
  "- GitHub CLI auth: $GhAuth"
  ""
  "## VS Code Extensions"
)

$extensions = @(code --list-extensions 2>$null)
foreach ($ext in @("ms-vscode.powershell","saoudrizwan.claude-dev","anthropic.claude-code","dbaeumer.vscode-eslint","esbenp.prettier-vscode")) {
  $status = if ($extensions -contains $ext) { "installed" } else { "missing" }
  $lines += "- ${ext}: $status"
}

$lines += @(
  ""
  "## Ollama"
  '```text'
  ((ollama list 2>&1) -join "`n")
  '```'
  ""
  "## Scheduled Tasks"
  '```text'
  ((Get-ScheduledTask -TaskName 'Local Web AI Worker','Local Ollama Auto Start','Local Free Claude Code Proxy Auto Start' -ErrorAction SilentlyContinue | Select-Object TaskName,State | Format-Table -AutoSize | Out-String).Trim())
  '```'
)

$lines | Set-Content -LiteralPath $Report -Encoding utf8
Write-Host "Doctor report: $Report"
Write-Host ($lines -join "`n")
