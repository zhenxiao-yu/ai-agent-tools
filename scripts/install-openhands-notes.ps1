$Docs = "C:\ai-agent-tools\configs\OPENHANDS_SETUP.md"
Write-Host "OpenHands is optional and Docker/WSL-heavy on Windows."
Write-Host "This script does not install Docker, WSL, or OpenHands automatically."
Write-Host "Opening setup notes: $Docs"
Start-Process $Docs | Out-Null
