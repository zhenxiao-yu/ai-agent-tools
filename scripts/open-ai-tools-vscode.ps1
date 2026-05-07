param(
  [switch]$OpenDashboard
)

$ErrorActionPreference = "Stop"
$Workspace = "C:\ai-agent-tools\Local AI Control Center.code-workspace"

if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
  throw "VS Code CLI 'code' was not found on PATH. Open VS Code and run 'Shell Command: Install code command in PATH', or reinstall VS Code."
}

Write-Host "[vscode] Opening workspace: $Workspace"
code $Workspace

if ($OpenDashboard) {
  Write-Host "[vscode] Opening dashboard too."
  & "C:\ai-agent-tools\scripts\open-dashboard.ps1"
}
