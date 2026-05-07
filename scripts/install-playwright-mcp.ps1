$ErrorActionPreference = "Stop"
$answer = Read-Host "Install Playwright MCP globally with npm and install Chromium? Type YES to continue"
if ($answer -ne "YES") {
  Write-Host "No changes made."
  exit 0
}
npm install -g @playwright/mcp
npx playwright install chromium
Write-Host "Playwright MCP install attempted. Test with: npx @playwright/mcp --help"
