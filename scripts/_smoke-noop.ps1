<#
.SYNOPSIS
    Tiny no-op script used by the dashboard async-job smoke test.

.DESCRIPTION
    Exercises both a value-bearing parameter and a switch so regressions in the
    wrapper's argument forwarding (scripts/_run-job.ps1) get caught immediately.
#>

[CmdletBinding()]
param(
    [string]$Message = "noop",
    [switch]$Loud
)

if ($Loud) {
    Write-Host "NOOP RAN LOUDLY: $Message"
}
else {
    Write-Host "noop ran: $Message"
}

exit 0
