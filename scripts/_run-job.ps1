<#
.SYNOPSIS
    Internal wrapper for the dashboard async job system. Runs a target script,
    captures all output streams to logs/jobs/<id>.log, and writes
    logs/jobs/<id>.exit with the inner script's exit code.

.PARAMETER JobId
    Job identifier minted by dashboard/jobs.py. Drives the log and exit-marker
    file names.

.PARAMETER ScriptPath
    Absolute path to the PowerShell script to execute.

.PARAMETER Forward
    Remaining arguments passed through to the target script. Use ``--`` on the
    parent command line to separate them from the wrapper's own parameters.

.NOTES
    Not intended to be called directly. The dashboard spawns this detached and
    polls the exit-marker file to learn when the inner script has finished.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$JobId,

    [Parameter(Mandatory = $true)]
    [string]$ScriptPath,

    [string]$ForwardJson = ""
)

# Don't let an inner failure abort the wrapper before we can record an exit code.
$ErrorActionPreference = "Continue"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$Root = "C:\ai-agent-tools"
$JobsDir = Join-Path $Root "logs\jobs"
$LogPath = Join-Path $JobsDir "$JobId.log"
$ExitPath = Join-Path $JobsDir "$JobId.exit"

New-Item -ItemType Directory -Path $JobsDir -Force | Out-Null

# The dashboard packages forwarded args as base64(JSON([...])) to avoid any
# PowerShell parameter-binding collisions on inner flags.
$argList = @()
if ($ForwardJson) {
    try {
        $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($ForwardJson))
        $parsed = $decoded | ConvertFrom-Json
        if ($parsed -is [System.Array]) {
            $argList = @($parsed | ForEach-Object { [string]$_ })
        }
        elseif ($null -ne $parsed) {
            $argList = @([string]$parsed)
        }
    }
    catch {
        "[wrapper] failed to decode ForwardJson: $($_.Exception.Message)" |
            Out-File -LiteralPath (Join-Path "C:\ai-agent-tools\logs\jobs" "$JobId.log") -Append -Encoding utf8
    }
}

# PowerShell array-splat (`& $script @array`) binds positionally, so flags like
# `-RepoPath` arrive as positional values and the inner script rejects them.
# Convert the flat ["-Foo","bar","-Switch"] form into a hashtable and splat
# that instead. Hashtable splat performs name binding.
function ConvertTo-ParamHash {
    param([string[]]$Items)

    $hash = @{}
    $i = 0
    while ($i -lt $Items.Count) {
        $cur = [string]$Items[$i]
        if ($cur.StartsWith('-') -and $cur.Length -gt 1) {
            $name = $cur.Substring(1)
            $hasNext = ($i + 1) -lt $Items.Count
            if ($hasNext -and -not ([string]$Items[$i + 1]).StartsWith('-')) {
                $hash[$name] = [string]$Items[$i + 1]
                $i += 2
                continue
            }
            $hash[$name] = $true   # switch parameter
            $i += 1
            continue
        }
        # Positional or malformed leading value — keep moving.
        $i += 1
    }
    return $hash
}

$paramHash = ConvertTo-ParamHash -Items $argList

"[wrapper] $((Get-Date).ToString('o')) start $ScriptPath" | Out-File -LiteralPath $LogPath -Append -Encoding utf8
if ($argList.Count -gt 0) {
    "[wrapper] args: $($argList -join ' ')" | Out-File -LiteralPath $LogPath -Append -Encoding utf8
}

$exit = 0
try {
    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        throw "Script not found: $ScriptPath"
    }

    # Merge every output stream into success (`*>&1`) so Write-Host, errors,
    # warnings, verbose, and information all reach the log. Out-File with
    # explicit UTF-8 avoids PowerShell 5.1's default UTF-16-LE host encoding
    # which produces garbled space-interleaved text when read as UTF-8.
    & $ScriptPath @paramHash *>&1 | Out-String -Stream | Out-File -LiteralPath $LogPath -Append -Encoding utf8
    $exit = $LASTEXITCODE
    if ($null -eq $exit) { $exit = 0 }
}
catch {
    "[wrapper] EXCEPTION: $($_.Exception.Message)" | Out-File -LiteralPath $LogPath -Append -Encoding utf8
    $exit = 1
}

"[wrapper] $((Get-Date).ToString('o')) exit=$exit" | Out-File -LiteralPath $LogPath -Append -Encoding utf8

# Write the exit marker last so the dashboard treats the job as done only after
# the log is fully flushed.
[System.IO.File]::WriteAllText($ExitPath, "$exit", [System.Text.Encoding]::ASCII)

exit $exit
