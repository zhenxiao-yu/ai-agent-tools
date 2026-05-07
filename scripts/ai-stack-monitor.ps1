param(
  [switch]$Watch,
  [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Continue"
$Root = "C:\ai-agent-tools"

function Test-Http([string]$Uri, [hashtable]$Headers = @{}) {
  try {
    Invoke-RestMethod -Uri $Uri -Headers $Headers -TimeoutSec 3 -ErrorAction Stop | Out-Null
    return "yes"
  } catch {
    return "no"
  }
}

function Show-Monitor {
  Clear-Host
  Write-Host "Local AI Stack Monitor"
  Write-Host "======================"
  Write-Host "Time: $(Get-Date)"
  Write-Host ""
  Write-Host "Ollama API: $(Test-Http 'http://127.0.0.1:11434/api/tags')"
  Write-Host "free-claude-code proxy: $(Test-Http 'http://127.0.0.1:8082/v1/models' @{ 'x-api-key'='freecc' })"
  Write-Host ""
  Write-Host "Ports:"
  Get-NetTCPConnection -LocalPort 11434,8082 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize
  Write-Host "Models:"
  try { ollama list } catch { Write-Host "ollama list failed: $($_.Exception.Message)" }
  Write-Host ""
  Write-Host "Running models / GPU hint:"
  try { ollama ps } catch { Write-Host "ollama ps failed: $($_.Exception.Message)" }
  Write-Host ""
  Write-Host "Tools:"
  Write-Host "Aider: $(if ((Get-Command aider -ErrorAction SilentlyContinue) -or (Test-Path \"$env:USERPROFILE\.local\bin\aider.exe\")) { 'yes' } else { 'no' })"
  Write-Host "Cline extension: $(if ((code --list-extensions 2>$null) -match 'saoudrizwan\.claude-dev') { 'yes' } else { 'no' })"
  Write-Host "GitHub CLI auth:"
  gh auth status 2>&1 | Select-Object -First 8 | ForEach-Object { Write-Host "  $_" }
  Write-Host ""
  Write-Host "Scheduled tasks:"
  Get-ScheduledTask -TaskName "Local Web AI Worker","Local Ollama Auto Start","Local Free Claude Code Proxy Auto Start" -ErrorAction SilentlyContinue | Select-Object TaskName,State | Format-Table -AutoSize
  Write-Host "Disk:"
  Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -in @("C","H") } | Select-Object Name,@{n="FreeGB";e={[math]::Round($_.Free/1GB,2)}},@{n="UsedGB";e={[math]::Round($_.Used/1GB,2)}} | Format-Table -AutoSize
  Write-Host "RAM:"
  Get-CimInstance Win32_OperatingSystem | Select-Object @{n="TotalGB";e={[math]::Round($_.TotalVisibleMemorySize/1MB,2)}},@{n="FreeGB";e={[math]::Round($_.FreePhysicalMemory/1MB,2)}} | Format-Table -AutoSize
  Write-Host "Latest logs:"
  Get-ChildItem -LiteralPath (Join-Path $Root "logs") -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime | Format-Table -AutoSize
  Write-Host "Latest reports:"
  Get-ChildItem -LiteralPath (Join-Path $Root "reports") -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime | Format-Table -AutoSize
}

do {
  Show-Monitor
  if ($Watch) { Start-Sleep -Seconds $IntervalSeconds }
} while ($Watch)
