$ErrorActionPreference = "Stop"
$DesktopShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Local AI Control Center.lnk"
$StartMenuDir = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs"
$StartMenuShortcutPath = Join-Path $StartMenuDir "Local AI Control Center.lnk"
$Target = (Get-Command powershell).Source
$ScriptPath = "C:\ai-agent-tools\scripts\open-dashboard.ps1"
$Arguments = "-ExecutionPolicy Bypass -File `"$ScriptPath`""

function New-LocalAiShortcut([string]$ShortcutPath) {
  if (Test-Path -LiteralPath $ShortcutPath) {
    $answer = Read-Host "Shortcut already exists: $ShortcutPath. Overwrite it? Type YES to overwrite"
    if ($answer -ne "YES") {
      Write-Host "Shortcut not changed: $ShortcutPath"
      return
    }
  }
  try {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $Target
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = "C:\ai-agent-tools"
    $shortcut.Description = "Open the Local AI Control Center"
    $shortcut.IconLocation = "$Target,0"
    $shortcut.Save()
    Write-Host "Created shortcut: $ShortcutPath"
  } catch {
    Write-Host "Could not create shortcut directly at $ShortcutPath"
    throw
  }
}

$answerStart = Read-Host "Create Start Menu shortcut too? Type YES to create"
if ($answerStart -eq "YES") {
  New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null
  New-LocalAiShortcut $StartMenuShortcutPath
} else {
  Write-Host "Start Menu shortcut skipped."
}

try {
  New-LocalAiShortcut $DesktopShortcutPath
} catch {
  if (Test-Path -LiteralPath $StartMenuShortcutPath) {
    Write-Host "Trying Desktop fallback by copying the Start Menu shortcut."
    Remove-Item -LiteralPath $DesktopShortcutPath -Force -ErrorAction SilentlyContinue
    Copy-Item -LiteralPath $StartMenuShortcutPath -Destination $DesktopShortcutPath -Force
    Write-Host "Created shortcut: $DesktopShortcutPath"
  } else {
    throw
  }
}
