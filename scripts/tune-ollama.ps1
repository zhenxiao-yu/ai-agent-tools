<#
.SYNOPSIS
    Polish a local Ollama setup: persist sane environment variables, list
    recommended coding models, and report GPU/VRAM if available.

.DESCRIPTION
    Designed to be run from the dashboard "Tune Ollama" button. Idempotent:
    a second run just confirms the current state without changing it.

    What it does:

      1. Sets per-user environment variables that materially improve daily
         use (kept off by default in a stock Ollama install):

           OLLAMA_KEEP_ALIVE   = 30m   (keep model warm between dashboard
                                        actions instead of cold-loading
                                        on every request)
           OLLAMA_NUM_PARALLEL = 2     (allow worker + reviewer to run
                                        concurrently on the same model)
           OLLAMA_MAX_LOADED_MODELS = 2 (avoid full unload when switching
                                         between coder + planner)

         Use -Reset to clear them.

      2. Lists installed models with size and family.

      3. Reports GPU / VRAM when nvidia-smi is on PATH.

      4. With -InstallRecommended, pulls a curated short list of coding
         models (qwen2.5-coder, deepseek-coder-v2, llama3.1) sized for
         daily use. Skipped models are reported.

.PARAMETER Reset
    Remove the persisted Ollama env vars instead of setting them.

.PARAMETER InstallRecommended
    Run ``ollama pull`` for the recommended model set.

.PARAMETER ModelsToPull
    Explicit list of model tags to pull, overriding the curated set.
#>

[CmdletBinding()]
param(
    [switch]$Reset,
    [switch]$InstallRecommended,
    [string[]]$ModelsToPull
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Step([string]$Message) { Write-Host "[tune-ollama] $Message" }

# --- Resolve ollama -----------------------------------------------------
function Resolve-Ollama {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidate = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path -LiteralPath $candidate) { return $candidate }
    return $null
}

$OllamaExe = Resolve-Ollama
if (-not $OllamaExe) {
    Write-Warning "Ollama executable was not found. Install it before tuning."
}
else {
    Step "Ollama: $OllamaExe"
}

# --- Env tuning ---------------------------------------------------------
$EnvDefaults = [ordered]@{
    OLLAMA_KEEP_ALIVE        = "30m"
    OLLAMA_NUM_PARALLEL      = "2"
    OLLAMA_MAX_LOADED_MODELS = "2"
}

if ($Reset) {
    Step "Resetting Ollama env vars."
    foreach ($name in $EnvDefaults.Keys) {
        [Environment]::SetEnvironmentVariable($name, $null, "User")
        Remove-Item -Path "Env:$name" -ErrorAction SilentlyContinue
        Step "  unset $name"
    }
}
else {
    Step "Persisting Ollama env vars (User scope)."
    foreach ($entry in $EnvDefaults.GetEnumerator()) {
        $name = $entry.Key
        $desired = $entry.Value
        $current = [Environment]::GetEnvironmentVariable($name, "User")
        if ($current -eq $desired) {
            Step "  $name already = $desired"
        }
        else {
            [Environment]::SetEnvironmentVariable($name, $desired, "User")
            Set-Item -Path "Env:$name" -Value $desired
            Step "  $name = $desired (was: $(if ($current) { $current } else { '<unset>' }))"
        }
    }
    Step "Restart Ollama (or sign out / back in) for env changes to take effect."
}

# --- Installed models ---------------------------------------------------
if ($OllamaExe) {
    Step ""
    Step "Installed models:"
    $listOutput = & $OllamaExe list 2>$null
    if ($listOutput) {
        $listOutput | ForEach-Object { Write-Host "  $_" }
    }
    else {
        Step "  (none installed yet)"
    }
}

# --- GPU / VRAM ---------------------------------------------------------
Step ""
Step "GPU info:"
$nvidia = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidia) {
    & $nvidia.Source --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader 2>$null |
        ForEach-Object { Write-Host "  $_" }
}
else {
    Step "  nvidia-smi not on PATH (CPU-only or non-NVIDIA GPU; Ollama can still run)."
}

# --- Recommended models -------------------------------------------------
$Recommended = @(
    [pscustomobject]@{ Tag = "qwen2.5-coder:7b";   Role = "fast coder";       SizeGb = 4.7 }
    [pscustomobject]@{ Tag = "qwen2.5-coder:14b";  Role = "default coder";    SizeGb = 9.0 }
    [pscustomobject]@{ Tag = "llama3.1:8b";        Role = "planner / chat";   SizeGb = 4.7 }
)

Step ""
Step "Recommended coding models:"
foreach ($m in $Recommended) {
    Write-Host ("  - {0,-26} ({1,5} GB)  {2}" -f $m.Tag, $m.SizeGb, $m.Role)
}

if ($InstallRecommended -or $ModelsToPull) {
    if (-not $OllamaExe) { throw "Cannot pull models: ollama executable not found." }

    $tagsToPull = if ($ModelsToPull) { $ModelsToPull } else { $Recommended.Tag }
    $installed = (& $OllamaExe list 2>$null) -join "`n"

    Step ""
    Step "Pulling models (may take a while)..."
    foreach ($tag in $tagsToPull) {
        if ($installed -match [regex]::Escape($tag)) {
            Step "  $tag already installed; skipping."
            continue
        }
        Step "  ollama pull $tag"
        & $OllamaExe pull $tag
        if ($LASTEXITCODE -ne 0) {
            Step "  WARN: pull failed for $tag (exit $LASTEXITCODE)"
        }
    }
}
else {
    Step ""
    Step "Run with -InstallRecommended to pull the curated set, or pass -ModelsToPull <tags>."
}

Step "Done."
exit 0
