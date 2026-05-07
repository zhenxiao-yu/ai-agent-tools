$ErrorActionPreference = "Continue"
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
  Write-Host "Docker CLI is missing. Nothing to stop."
  exit 0
}
docker stop openhands-app 2>&1
Write-Host "OpenHands stop requested."
