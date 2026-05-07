param(
  [int]$Port = 3000
)

$ErrorActionPreference = "Stop"
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
  Write-Host "Docker CLI is missing. OpenHands local GUI on Windows requires Docker Desktop + WSL 2."
  Write-Host "Read: C:\ai-agent-tools\configs\OPENHANDS_SETUP.md"
  exit 2
}

try {
  Invoke-WebRequest -Uri "http://127.0.0.1:$Port" -TimeoutSec 3 -UseBasicParsing | Out-Null
  Write-Host "OpenHands already appears online at http://127.0.0.1:$Port"
  Start-Process "http://127.0.0.1:$Port" | Out-Null
  exit 0
} catch {}

Write-Host "Starting OpenHands with Docker on http://127.0.0.1:$Port"
Write-Host "Use OpenHands settings: custom model openai/qwen2.5-coder:14b, base URL http://host.docker.internal:11434/v1, API key local-llm."
docker run -d --rm --pull=always `
  -e AGENT_SERVER_IMAGE_REPOSITORY=ghcr.io/openhands/agent-server `
  -e AGENT_SERVER_IMAGE_TAG=1.19.1-python `
  -e LOG_ALL_EVENTS=true `
  -v /var/run/docker.sock:/var/run/docker.sock `
  -v "${env:USERPROFILE}\.openhands:/.openhands" `
  -p "${Port}:3000" `
  --add-host host.docker.internal:host-gateway `
  --name openhands-app `
  docker.openhands.dev/openhands/openhands:1.7
Start-Process "http://127.0.0.1:$Port" | Out-Null
