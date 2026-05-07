<#
.SYNOPSIS
    Disable and remove the optional Local Web AI Worker scheduled task.
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$TaskName = "Local Web AI Worker"
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Task) {
    Disable-ScheduledTask -TaskName $TaskName | Out-Null
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Scheduled task disabled and removed: $TaskName"
    exit 0
}

Write-Host "Scheduled task not found: $TaskName"
exit 0
