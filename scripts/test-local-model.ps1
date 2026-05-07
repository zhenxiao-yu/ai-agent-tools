param(
    [string]$Model = "qwen2.5-coder:14b"
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}
$Root = "C:\ai-agent-tools"
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogDir "model-test-$Timestamp.log"
$Prompt = "Write a small TypeScript function that validates an email address and explain it briefly."

try {
    "Model: $Model" | Tee-Object -FilePath $LogPath
    "Timestamp: $Timestamp" | Tee-Object -FilePath $LogPath -Append
    "Prompt: $Prompt" | Tee-Object -FilePath $LogPath -Append
    "" | Tee-Object -FilePath $LogPath -Append

    $Started = Get-Date
    $Body = @{
        model  = $Model
        prompt = $Prompt
        stream = $false
    } | ConvertTo-Json -Depth 5
    $Result = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/generate" -Method Post -ContentType "application/json" -Body $Body -TimeoutSec 900
    $Elapsed = (Get-Date) - $Started

    $Result.response | Tee-Object -FilePath $LogPath -Append
    "" | Tee-Object -FilePath $LogPath -Append
    "ElapsedSeconds: $([math]::Round($Elapsed.TotalSeconds, 2))" | Tee-Object -FilePath $LogPath -Append

    if (-not $Result.response) {
        throw "Ollama returned an empty response."
    }

    Write-Host "Model test succeeded: $Model"
    Write-Host "Log: $LogPath"
    exit 0
}
catch {
    "ERROR: $($_.Exception.Message)" | Tee-Object -FilePath $LogPath -Append
    Write-Error "Model test failed. Log: $LogPath"
    exit 1
}
