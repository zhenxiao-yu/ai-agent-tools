param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}
$LogDir = "C:\ai-agent-tools\logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogDir "github-pipelines-$Timestamp.log"

if (-not (Test-Path -LiteralPath $RepoPath)) {
    throw "RepoPath does not exist: $RepoPath"
}

Push-Location $RepoPath
try {
    if (-not (Test-Path ".git")) {
        throw "Not a git repository: $RepoPath"
    }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI is not installed or not on PATH."
    }

    "Repo: $RepoPath" | Tee-Object -FilePath $LogPath
    "Timestamp: $Timestamp" | Tee-Object -FilePath $LogPath -Append
    "" | Tee-Object -FilePath $LogPath -Append
    "== gh run list --limit 10 ==" | Tee-Object -FilePath $LogPath -Append
    gh run list --limit 10 2>&1 | Tee-Object -FilePath $LogPath -Append

    $LatestRun = gh run list --limit 1 --json databaseId --jq ".[0].databaseId" 2>$null
    if ($LatestRun) {
        "" | Tee-Object -FilePath $LogPath -Append
        "== gh run view $LatestRun --log ==" | Tee-Object -FilePath $LogPath -Append
        gh run view $LatestRun --log 2>&1 | Tee-Object -FilePath $LogPath -Append
    }
    else {
        "No GitHub Actions runs found." | Tee-Object -FilePath $LogPath -Append
    }

    Write-Host "GitHub pipeline log saved to: $LogPath"
}
finally {
    Pop-Location
}
