#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$BackupDir
)

$ErrorActionPreference = 'Stop'
$BackupRoot = 'C:\ai-agent-tools\terminal-backups'

if (-not $BackupDir) {
    $BackupDir = Get-ChildItem -LiteralPath $BackupRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $BackupDir -or -not (Test-Path -LiteralPath $BackupDir)) {
    throw "No backup directory found. Pass -BackupDir with a valid path under $BackupRoot."
}

$manifestPath = Join-Path $BackupDir 'rollback-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Rollback manifest not found: $manifestPath"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (-not $manifest) {
    Write-Warning "Manifest is empty; no files to restore."
    return
}

foreach ($item in @($manifest)) {
    if (-not (Test-Path -LiteralPath $item.BackupPath)) {
        Write-Warning "Backup file missing, skipped: $($item.BackupPath)"
        continue
    }
    $parent = Split-Path -Parent $item.OriginalPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Copy-Item -LiteralPath $item.BackupPath -Destination $item.OriginalPath -Force
    Write-Host "Restored $($item.OriginalPath) from $($item.BackupPath)"
}

Write-Host "Rollback complete from $BackupDir"
