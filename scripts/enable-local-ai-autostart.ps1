param(
  [switch]$EnableProxy
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "[local-ai-autostart] Enabling Ollama auto-start at Windows login."
& (Join-Path $Root "scripts\ensure-ollama-autostart.ps1")

if (-not $EnableProxy) {
  Write-Host "[local-ai-autostart] Free Claude Code proxy auto-start was not enabled."
  Write-Host "[local-ai-autostart] To enable it later, rerun this script with -EnableProxy after you are comfortable with manual proxy use."
  exit 0
}

$TaskName = "Local Free Claude Code Proxy Auto Start"
$pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }
$script = Join-Path $Root "scripts\start-free-claude-code-proxy.ps1"
$action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
  Write-Host "[local-ai-autostart] Updating existing proxy auto-start task."
  Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
} else {
  Write-Host "[local-ai-autostart] Creating proxy auto-start task."
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Starts local free-claude-code proxy for local Claude Code compatibility." | Out-Null
}

Write-Host "[local-ai-autostart] Proxy auto-start enabled."
