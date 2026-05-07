param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

if (-not (Test-Path -LiteralPath $RepoPath)) { throw "RepoPath does not exist: $RepoPath" }

Push-Location $RepoPath
try {
    if (-not (Test-Path "package.json")) { throw "package.json not found: $RepoPath" }

    Write-Host "This will modify the repo by installing @playwright/test and possibly adding tests/smoke.spec.ts."
    $Confirm = Read-Host "Type YES to continue"
    if ($Confirm -ne "YES") {
        Write-Host "Cancelled."
        return
    }

    npm install -D @playwright/test
    if ($LASTEXITCODE -ne 0) { throw "npm install -D @playwright/test failed." }

    npx playwright install
    if ($LASTEXITCODE -ne 0) { throw "npx playwright install failed." }

    New-Item -ItemType Directory -Path "tests" -Force | Out-Null
    $SmokePath = "tests\smoke.spec.ts"
    if (-not (Test-Path $SmokePath)) {
        @"
import { test, expect } from '@playwright/test';

test('smoke: app renders without server errors', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('body')).toBeVisible();
  await expect(page.locator('body')).not.toContainText('404');
  await expect(page.locator('body')).not.toContainText('Internal Server Error');
});
"@ | Set-Content -Path $SmokePath -Encoding UTF8
        Write-Host "Created $SmokePath"
    }
    else {
        Write-Host "$SmokePath already exists; not overwriting."
    }

    $AddScript = Read-Host "Type YES to add package.json script `"e2e`": `"playwright test`""
    if ($AddScript -eq "YES") {
        $Package = Get-Content -Raw -Path "package.json" | ConvertFrom-Json
        if (-not $Package.scripts) {
            $Package | Add-Member -MemberType NoteProperty -Name scripts -Value ([PSCustomObject]@{})
        }
        if (-not ($Package.scripts.PSObject.Properties.Name -contains "e2e")) {
            $Package.scripts | Add-Member -MemberType NoteProperty -Name e2e -Value "playwright test"
            $Package | ConvertTo-Json -Depth 20 | Set-Content -Path "package.json" -Encoding UTF8
            Write-Host "Added e2e script."
        }
        else {
            Write-Host "e2e script already exists; not changing it."
        }
    }
}
finally {
    Pop-Location
}
