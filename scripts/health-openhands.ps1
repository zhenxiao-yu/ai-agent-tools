$ErrorActionPreference = "Continue"
Write-Host "OpenHands Health"
Write-Host "==============="
$docker = Get-Command docker -ErrorAction SilentlyContinue
Write-Host "Docker CLI: $(if ($docker) { $docker.Source } else { 'missing' })"
if ($docker) {
  docker ps --filter "name=openhands" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1
}
try {
  Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 3 -UseBasicParsing | Out-Null
  Write-Host "OpenHands URL: online at http://127.0.0.1:3000"
} catch {
  Write-Host "OpenHands URL: offline"
}
