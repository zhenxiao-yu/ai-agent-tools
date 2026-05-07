$ErrorActionPreference = "Stop"
$Tasks = @("Local Ollama Auto Start", "Local Free Claude Code Proxy Auto Start")

foreach ($taskName in $Tasks) {
  $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($task) {
    Write-Host "[local-ai-autostart] Disabling and unregistering '$taskName'."
    Disable-ScheduledTask -TaskName $taskName | Out-Null
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
  } else {
    Write-Host "[local-ai-autostart] Task '$taskName' was not present."
  }
}

Write-Host "[local-ai-autostart] Done. Ollama, models, configs, and tools were not uninstalled or deleted."
