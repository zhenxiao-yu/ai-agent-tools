param(
  [Parameter(Mandatory=$true)][string]$RepoPath,
  [string]$Model = "ollama/qwen2.5-coder:14b"
)

$ErrorActionPreference = "Stop"
$Allowlist = "C:\ai-agent-tools\configs\repo-allowlist.txt"

function Normalize([string]$Path) {
  return ([System.IO.Path]::GetFullPath($Path)).TrimEnd('\').ToLowerInvariant()
}

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "Repo path does not exist: $RepoPath" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) { throw "Not a Git repo: $RepoPath" }
$allowed = Get-Content -LiteralPath $Allowlist -ErrorAction Stop | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") } | ForEach-Object { Normalize $_.Trim() }
if ($allowed -notcontains (Normalize $RepoPath)) { throw "Repo is not allowlisted: $RepoPath" }

$aider = Get-Command aider -ErrorAction SilentlyContinue
if (-not $aider) {
  $candidate = Join-Path $env:USERPROFILE ".local\bin\aider.exe"
  if (Test-Path -LiteralPath $candidate) { $aider = [pscustomobject]@{ Source = $candidate } }
}
if (-not $aider) { throw "Aider was not found." }

Write-Host "Starting Aider Browser UI for: $RepoPath"
Write-Host "WARNING: Aider Browser UI can edit files. This launcher uses --no-auto-commits and does not push."
Set-Location $RepoPath
& $aider.Source --browser --model $Model --no-auto-commits
