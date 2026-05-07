param(
  [string]$TaskName = "Local Ollama Auto Start"
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "ollama-autostart.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Step([string]$Message) {
  Write-Host "[ollama-autostart] $Message"
}

function Test-OllamaApi {
  try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Resolve-Ollama {
  $cmd = Get-Command ollama -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $candidate = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
  if (Test-Path -LiteralPath $candidate) { return $candidate }
  throw "Ollama executable was not found on PATH or in the default Windows install path."
}

Write-Step "Checking Ollama executable."
$OllamaExe = Resolve-Ollama
Write-Step "Ollama executable: $OllamaExe"

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }

$safeOllama = $OllamaExe.Replace("'", "''")
$safeLog = $LogPath.Replace("'", "''")
$command = "& { New-Item -ItemType Directory -Force -Path 'C:\ai-agent-tools\logs' | Out-Null; &'$safeOllama' serve *>> '$safeLog' }"
$action = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$command`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Days 3650)

if ($task) {
  Write-Step "Scheduled task already exists. Updating it to the safe local command."
  Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
} else {
  Write-Step "Creating scheduled task '$TaskName' at user login."
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Starts local Ollama for local AI tools at Windows login." | Out-Null
}

if (Test-OllamaApi) {
  Write-Step "Ollama API is already responding."
  exit 0
}

Write-Step "Ollama API is not responding. Starting Ollama now."
$startCommand = "&'$safeOllama' serve *>> '$safeLog'"
Start-Process -FilePath $pwsh -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-Command",$startCommand) -WindowStyle Hidden | Out-Null

for ($i = 1; $i -le 20; $i++) {
  Start-Sleep -Seconds 1
  if (Test-OllamaApi) {
    Write-Step "Ollama API is responding."
    exit 0
  }
}

Write-Error "Ollama did not respond after startup attempt. See $LogPath"
exit 1
