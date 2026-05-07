$ErrorActionPreference = "Continue"
$Root = "C:\ai-agent-tools"

function Test-Http([string]$Uri) {
  try {
    Invoke-RestMethod -Uri $Uri -TimeoutSec 3 -ErrorAction Stop | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Test-Proxy([string]$Uri) {
  try {
    Invoke-RestMethod -Uri $Uri -Headers @{ "x-api-key" = "freecc" } -TimeoutSec 3 -ErrorAction Stop | Out-Null
    return $true
  } catch {
    return $false
  }
}

Write-Host "Local AI Stack Health"
Write-Host "====================="

$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
Write-Host "Ollama executable: $($ollamaCmd.Source)"
Write-Host "Ollama API 11434: $(if (Test-Http 'http://127.0.0.1:11434/api/tags') { 'yes' } else { 'no' })"

Write-Host ""
Write-Host "Ollama models:"
try { ollama list } catch { Write-Host "ollama list failed: $($_.Exception.Message)" }

Write-Host ""
try {
  $models = (ollama list 2>$null) -join "`n"
  Write-Host "Default qwen2.5-coder:14b available: $(if ($models -match 'qwen2\.5-coder:14b') { 'yes' } else { 'no' })"
} catch {
  Write-Host "Default qwen2.5-coder:14b available: unknown"
}

Write-Host "free-claude-code proxy 8082: $(if (Test-Proxy 'http://127.0.0.1:8082/v1/models') { 'yes' } else { 'no' })"

Write-Host ""
Write-Host "Ports:"
Get-NetTCPConnection -LocalPort 11434,8082 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize

Write-Host "VS Code Cline extension installed: $(if ((code --list-extensions 2>$null) -match 'saoudrizwan\.claude-dev') { 'yes' } else { 'no' })"
Write-Host "Claude Code CLI detected: $(if (Get-Command claude -ErrorAction SilentlyContinue) { 'yes' } else { 'no' })"
Write-Host "Aider detected: $(if (Get-Command aider -ErrorAction SilentlyContinue) { 'yes' } elseif (Test-Path "$env:USERPROFILE\.local\bin\aider.exe") { 'yes, at user local bin' } else { 'no' })"

Write-Host ""
Write-Host "Ollama running models / GPU hint:"
try { ollama ps } catch { Write-Host "ollama ps failed: $($_.Exception.Message)" }
