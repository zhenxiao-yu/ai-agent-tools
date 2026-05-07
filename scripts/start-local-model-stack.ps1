param(
  [string]$Model = "qwen2.5-coder:14b",
  [switch]$StartProxy,
  [switch]$SkipProxyTest
)

$ErrorActionPreference = "Stop"
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Step([string]$Message) { Write-Host "[local-ai-stack] $Message" }

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
  throw "Ollama executable was not found."
}

$OllamaExe = Resolve-Ollama
Write-Step "Ollama: $OllamaExe"

if (-not (Test-OllamaApi)) {
  Write-Step "Ollama API is not responding. Starting Ollama."
  $log = Join-Path $LogDir "ollama-manual-start.log"
  $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
  if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }
  $safeOllama = $OllamaExe.Replace("'", "''")
  $safeLog = $log.Replace("'", "''")
  $cmd = "&'$safeOllama' serve *>> '$safeLog'"
  Start-Process -FilePath $pwsh -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-Command",$cmd) -WindowStyle Hidden | Out-Null
  for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-OllamaApi) { break }
  }
}

if (-not (Test-OllamaApi)) { throw "Ollama API is still not responding at http://127.0.0.1:11434" }
Write-Step "Ollama API is responding."

$modelList = ollama list
Write-Step "Installed models:"
$modelList | ForEach-Object { Write-Host $_ }
if (($modelList -join "`n") -notmatch [regex]::Escape($Model)) {
  throw "Required model '$Model' is not installed. Run: ollama pull $Model"
}

Write-Step "Running tiny model test."
$body = @{
  model = $Model
  prompt = "Reply with exactly: local-model-ok"
  stream = $false
  options = @{ num_predict = 16 }
} | ConvertTo-Json -Depth 5

$result = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 120
if (-not $result.response) { throw "Ollama model test returned no response." }
Write-Step "Model test response: $($result.response.Trim())"

if ($StartProxy -and -not $SkipProxyTest) {
  & (Join-Path $Root "scripts\start-free-claude-code-proxy.ps1") -Model $Model
}
