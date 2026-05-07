param(
  [ValidateSet("List","Set","Remove","Docs")]
  [string]$Action = "List",

  [ValidateSet("deepseek","qwen","kimi","siliconflow","openrouter","zai")]
  [string]$Provider
)

$ErrorActionPreference = "Stop"
$ProfilesPath = "C:\ai-agent-tools\configs\model-profiles.json"
$DocsPath = "C:\ai-agent-tools\configs\PROVIDER_KEYS_SETUP.md"

function Get-Profiles {
  $profiles = Get-Content -LiteralPath $ProfilesPath -Raw | ConvertFrom-Json
  $items = @()
  foreach ($prop in $profiles.PSObject.Properties) {
    $p = $prop.Value
    if ($p.apiKeyEnvVar) {
      $items += [pscustomobject]@{
        Profile = $prop.Name
        Provider = $p.provider
        EnvVar = $p.apiKeyEnvVar
        BaseUrl = $p.baseUrl
        Model = $p.model
        Paid = $p.paid
      }
    }
  }
  return $items
}

function Test-Key([string]$EnvVar) {
  return [bool]([Environment]::GetEnvironmentVariable($EnvVar, "Process") -or [Environment]::GetEnvironmentVariable($EnvVar, "User") -or [Environment]::GetEnvironmentVariable($EnvVar, "Machine"))
}

if ($Action -eq "Docs") {
  Write-Host "Opening provider key setup docs: $DocsPath"
  Start-Process $DocsPath | Out-Null
  exit 0
}

$profiles = @(Get-Profiles)
if ($Action -eq "List") {
  $profiles | Select-Object Provider,EnvVar,@{n="KeyPresent";e={ if (Test-Key $_.EnvVar) { "yes" } else { "no" } }},BaseUrl,Model,Paid | Format-Table -AutoSize
  exit 0
}

if (-not $Provider) { throw "Provider is required for -Action $Action." }
$profile = $profiles | Where-Object { $_.Provider -eq $Provider } | Select-Object -First 1
if (-not $profile) { throw "No API key profile found for provider '$Provider'." }

if ($Action -eq "Set") {
  Write-Host "Setting user-level key for $Provider ($($profile.EnvVar)). The key will not be printed."
  $secure = Read-Host "Paste API key" -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if (-not $plain) { throw "No key entered." }
    [Environment]::SetEnvironmentVariable($profile.EnvVar, $plain, "User")
  }
  finally {
    if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
  }
  Write-Host "Saved $($profile.EnvVar) to the user environment. Open a new terminal before testing."
  exit 0
}

if ($Action -eq "Remove") {
  $confirm = Read-Host "Remove user-level $($profile.EnvVar)? Type YES to remove"
  if ($confirm -ne "YES") {
    Write-Host "No change made."
    exit 0
  }
  [Environment]::SetEnvironmentVariable($profile.EnvVar, $null, "User")
  Write-Host "Removed user-level $($profile.EnvVar)."
}
