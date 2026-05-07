#requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Continue'
$Root = 'C:\ai-agent-tools'
$BackupRoot = Join-Path $Root 'terminal-backups'
$ScriptRoot = Join-Path $Root 'scripts'
$ReportRoot = Join-Path $Root 'reports'
$TerminalRoot = Join-Path $Root 'terminal'
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$BackupDir = Join-Path $BackupRoot $Stamp
$ReportPath = Join-Path $ReportRoot 'terminal-setup-report.md'
$ManifestPath = Join-Path $BackupDir 'rollback-manifest.json'
$ThemePath = Join-Path $TerminalRoot 'cyber-2026.omp.json'

$Installed = [System.Collections.Generic.List[string]]::new()
$Skipped = [System.Collections.Generic.List[string]]::new()
$Warnings = [System.Collections.Generic.List[string]]::new()
$Changed = [System.Collections.Generic.List[string]]::new()
$Backups = [System.Collections.Generic.List[object]]::new()

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Get-CommandPath {
    param([string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Backup-File {
    param([string]$Path, [string]$Label)
    if (Test-Path -LiteralPath $Path) {
        Ensure-Dir $BackupDir
        $safeName = ($Label -replace '[^a-zA-Z0-9._-]', '_')
        $dest = Join-Path $BackupDir $safeName
        Copy-Item -LiteralPath $Path -Destination $dest -Force
        $Backups.Add([pscustomobject]@{
            Label = $Label
            OriginalPath = $Path
            BackupPath = $dest
        })
        Write-Host "Backed up $Path -> $dest"
    }
}

function Install-WingetPackage {
    param(
        [string]$CommandName,
        [string]$PackageId,
        [string]$DisplayName
    )

    if (Get-CommandPath $CommandName) {
        $Skipped.Add("$DisplayName already installed")
        return
    }
    if ($SkipInstall) {
        $Skipped.Add("$DisplayName skipped by -SkipInstall")
        return
    }
    if (-not (Get-CommandPath 'winget')) {
        $Warnings.Add("winget unavailable; could not install $DisplayName")
        return
    }

    Write-Host "Installing $DisplayName via winget..."
    $args = @(
        'install', '--id', $PackageId, '--exact',
        '--source', 'winget',
        '--accept-package-agreements',
        '--accept-source-agreements',
        '--silent'
    )
    $process = Start-Process -FilePath 'winget' -ArgumentList $args -Wait -PassThru -NoNewWindow
    if ($process.ExitCode -eq 0) {
        $Installed.Add("$DisplayName ($PackageId)")
    } else {
        $Warnings.Add("winget install failed for $DisplayName ($PackageId), exit code $($process.ExitCode)")
    }
}

function Install-ModuleIfMissing {
    param([string]$Name)
    $module = Get-Module -ListAvailable -Name $Name | Sort-Object Version -Descending | Select-Object -First 1
    if ($module) {
        $Skipped.Add("$Name PowerShell module already installed")
        return
    }
    if ($SkipInstall) {
        $Skipped.Add("$Name PowerShell module skipped by -SkipInstall")
        return
    }
    try {
        Install-Module -Name $Name -Scope CurrentUser -Force -AllowClobber -Repository PSGallery
        $Installed.Add("$Name PowerShell module")
    } catch {
        $Warnings.Add("PowerShell module install failed for ${Name}: $($_.Exception.Message)")
    }
}

function Update-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

function Get-WindowsTerminalSettingsPath {
    $storePath = Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'
    $unpackagedPath = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json'
    if (Test-Path -LiteralPath $storePath) { return $storePath }
    if (Test-Path -LiteralPath $unpackagedPath) { return $unpackagedPath }
    Ensure-Dir (Split-Path -Parent $storePath)
    '{}' | Set-Content -LiteralPath $storePath -Encoding utf8
    return $storePath
}

function Add-Or-Replace-Keybinding {
    param(
        [object]$Settings,
        [string]$Keys,
        [object]$Command
    )

    if (-not $Settings.PSObject.Properties['keybindings'] -or -not $Settings.keybindings) {
        $Settings | Add-Member -NotePropertyName keybindings -NotePropertyValue @() -Force
    }
    $remaining = @($Settings.keybindings | Where-Object { $_.keys -ne $Keys })
    $remaining += [pscustomobject]@{ command = $Command; keys = $Keys }
    $Settings.keybindings = $remaining
}

function Add-Or-Replace-Scheme {
    param([object]$Settings, [object]$Scheme)
    if (-not $Settings.PSObject.Properties['schemes'] -or -not $Settings.schemes) {
        $Settings | Add-Member -NotePropertyName schemes -NotePropertyValue @() -Force
    }
    $Settings.schemes = @($Settings.schemes | Where-Object { $_.name -ne $Scheme.name })
    $Settings.schemes += $Scheme
}

function Add-Or-Replace-Profile {
    param([object]$Settings, [object]$Profile)
    if (-not $Settings.profiles.PSObject.Properties['list'] -or -not $Settings.profiles.list) {
        $Settings.profiles | Add-Member -NotePropertyName list -NotePropertyValue @() -Force
    }
    $Settings.profiles.list = @($Settings.profiles.list | Where-Object { $_.guid -ne $Profile.guid })
    $Settings.profiles.list += $Profile
}

function Write-OhMyPoshTheme {
    Ensure-Dir $TerminalRoot
    $theme = @'
{
  "$schema": "https://raw.githubusercontent.com/JanDeDobbeleer/oh-my-posh/main/themes/schema.json",
  "version": 3,
  "final_space": true,
  "blocks": [
    {
      "type": "prompt",
      "alignment": "left",
      "segments": [
        {
          "type": "session",
          "style": "diamond",
          "foreground": "#031018",
          "background": "#8BE9FD",
          "leading_diamond": "",
          "template": "  {{ .UserName }} ",
          "trailing_diamond": ""
        },
        {
          "type": "path",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#EAF6FF",
          "background": "#172033",
          "properties": {
            "style": "agnoster_short",
            "max_depth": 3
          },
          "template": " 󰉋 {{ .Path }} "
        },
        {
          "type": "git",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#071318",
          "background": "#7DF9C8",
          "background_templates": [
            "{{ if or (.Working.Changed) (.Staging.Changed) }}#F8D66D{{ end }}",
            "{{ if gt .Ahead 0 }}#FFB86B{{ end }}",
            "{{ if gt .Behind 0 }}#FF6B8A{{ end }}"
          ],
          "properties": {
            "branch_icon": " ",
            "fetch_status": true,
            "fetch_upstream_icon": true
          },
          "template": " {{ .HEAD }}{{ if .Working.Changed }} ±{{ .Working.String }}{{ end }}{{ if .Staging.Changed }} +{{ .Staging.String }}{{ end }} "
        },
        {
          "type": "node",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#06130B",
          "background": "#9AF7B2",
          "properties": {
            "fetch_package_manager": true
          },
          "template": "  {{ .Full }}{{ if .PackageManagerIcon }} {{ .PackageManagerIcon }}{{ end }} "
        },
        {
          "type": "python",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#071327",
          "background": "#9EC5FF",
          "template": "  {{ .Full }} "
        },
        {
          "type": "executiontime",
          "style": "powerline",
          "powerline_symbol": "",
          "foreground": "#F8FBFF",
          "background": "#8B5CF6",
          "properties": {
            "threshold": 350,
            "style": "roundrock"
          },
          "template": " 󱎫 {{ .FormattedMs }} "
        },
        {
          "type": "status",
          "style": "diamond",
          "foreground": "#041012",
          "background": "#2DFFB3",
          "background_templates": [
            "{{ if gt .Code 0 }}#FF4D7D{{ end }}"
          ],
          "trailing_diamond": "",
          "properties": {
            "always_enabled": true
          },
          "template": " {{ if gt .Code 0 }}✘ {{ .Code }}{{ else }}✓{{ end }} "
        }
      ]
    },
    {
      "type": "rprompt",
      "segments": [
        {
          "type": "time",
          "style": "plain",
          "foreground": "#8BE9FD",
          "properties": {
            "time_format": "15:04"
          },
          "template": "󰥔 {{ .CurrentDate | date .Format }}"
        }
      ]
    }
  ]
}
'@
    $theme | Set-Content -LiteralPath $ThemePath -Encoding utf8
    $Changed.Add("Wrote Oh My Posh theme: $ThemePath")
}

function Write-PowerShellProfile {
    param([string]$ProfilePath)
    Ensure-Dir (Split-Path -Parent $ProfilePath)
    $profileText = @'
# Beautiful Terminal 2026 profile
# Generated by C:\ai-agent-tools\scripts\setup-beautiful-terminal.ps1

# ----- Prompt ---------------------------------------------------------------
# Oh My Posh keeps the prompt compact while showing path, Git, runtime context,
# command duration, and success/failure state.
$ompTheme = 'C:\ai-agent-tools\terminal\cyber-2026.omp.json'
if (Get-Command oh-my-posh -ErrorAction SilentlyContinue) {
    oh-my-posh init pwsh --config $ompTheme | Invoke-Expression
}

# ----- Icons ----------------------------------------------------------------
# Terminal-Icons adds readable file/folder glyphs to common listings.
if (Get-Module -ListAvailable -Name Terminal-Icons) {
    Import-Module Terminal-Icons -ErrorAction SilentlyContinue
}

# ----- PSReadLine -----------------------------------------------------------
# Better editing, completion, prediction, and history search.
if (Get-Module -ListAvailable -Name PSReadLine) {
    Import-Module PSReadLine -ErrorAction SilentlyContinue
    Set-PSReadLineOption -EditMode Windows
    if (-not [Console]::IsOutputRedirected) {
        try {
            Set-PSReadLineOption -PredictionSource History -ErrorAction Stop
            Set-PSReadLineOption -PredictionViewStyle ListView -ErrorAction Stop
        } catch {
            # Prediction support depends on the host; keep startup quiet if unavailable.
        }
    }
    Set-PSReadLineOption -HistoryNoDuplicates
    Set-PSReadLineOption -BellStyle None
    Set-PSReadLineOption -CompletionQueryItems 100
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
    Set-PSReadLineKeyHandler -Key Ctrl+r -Function ReverseSearchHistory
    Set-PSReadLineKeyHandler -Key Ctrl+f -Function ForwardWord
    Set-PSReadLineKeyHandler -Key Ctrl+b -Function BackwardWord
    Set-PSReadLineKeyHandler -Key Ctrl+Backspace -Function BackwardKillWord
}

# ----- Navigation -----------------------------------------------------------
# zoxide learns frequently used directories and fzf powers fuzzy selection.
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression ((& zoxide init powershell) -join [Environment]::NewLine)
}
if (Get-Command fzf -ErrorAction SilentlyContinue) {
    $env:FZF_DEFAULT_OPTS = '--height 40% --layout=reverse --border --prompt="fzf> "'
}

# ----- Quality-of-life commands --------------------------------------------
function ll { Get-ChildItem -Force @args }
function la { Get-ChildItem -Force -Hidden @args }
function c { Clear-Host }
function gs { git status @args }
function gcmsg { git commit -m @args }
function gp { git push @args }
function gl { git log --oneline --graph --decorate @args }

function touch {
    param([Parameter(Mandatory)][string]$Path)
    if (Test-Path -LiteralPath $Path) {
        (Get-Item -LiteralPath $Path).LastWriteTime = Get-Date
    } else {
        New-Item -ItemType File -Path $Path | Out-Null
    }
}

function mkcd {
    param([Parameter(Mandatory)][string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
    Set-Location -LiteralPath $Path
}

function reload-profile {
    . $PROFILE
}

function edit-profile {
    if (Get-Command code -ErrorAction SilentlyContinue) {
        code $PROFILE
    } else {
        notepad $PROFILE
    }
}

function which {
    param([Parameter(Mandatory)][string]$Name)
    Get-Command $Name -ErrorAction SilentlyContinue | Select-Object Name, Source, CommandType
}

function ports {
    param([int]$Port)
    $connections = if ($Port) {
        Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    } else {
        Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue
    }
    $connections | ForEach-Object {
        $process = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        [pscustomobject]@{
            Port = $_.LocalPort
            Address = $_.LocalAddress
            ProcessId = $_.OwningProcess
            ProcessName = $process.ProcessName
        }
    } | Sort-Object Port, ProcessName
}

function kill-port {
    param([Parameter(Mandatory)][int]$Port)
    $connections = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Warning "No listening process found on port $Port."
        return
    }
    $connections | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {
        Stop-Process -Id $_ -Force
    }
}

# Prefer modern replacements when installed, while keeping PowerShell fallback.
if (Get-Command eza -ErrorAction SilentlyContinue) {
    function l { eza --icons --group-directories-first @args }
    function lt { eza --icons --tree --level=2 @args }
} elseif (Get-Command lsd -ErrorAction SilentlyContinue) {
    function l { lsd @args }
    function lt { lsd --tree --depth 2 @args }
}

if (Get-Command bat -ErrorAction SilentlyContinue) {
    function catp { bat --paging=never @args }
}
'@
    $profileText | Set-Content -LiteralPath $ProfilePath -Encoding utf8
    $Changed.Add("Updated PowerShell profile: $ProfilePath")
}

function Configure-WindowsTerminal {
    param([string]$SettingsPath)

    $raw = Get-Content -LiteralPath $SettingsPath -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) { $raw = '{}' }
    $settings = $raw | ConvertFrom-Json

    if (-not $settings.PSObject.Properties['profiles'] -or -not $settings.profiles) {
        $settings | Add-Member -NotePropertyName profiles -NotePropertyValue ([pscustomobject]@{ defaults = [pscustomobject]@{}; list = @() }) -Force
    }
    if (-not $settings.profiles.PSObject.Properties['defaults'] -or -not $settings.profiles.defaults) {
        $settings.profiles | Add-Member -NotePropertyName defaults -NotePropertyValue ([pscustomobject]@{}) -Force
    }

    $scheme = [pscustomobject]@{
        name = 'CleanGlass 2026'
        background = '#050812'
        foreground = '#E8F3FF'
        selectionBackground = '#223247'
        cursorColor = '#8BE9FD'
        black = '#07111F'
        red = '#FF4D7D'
        green = '#2DFFB3'
        yellow = '#F8D66D'
        blue = '#78A8FF'
        purple = '#B88CFF'
        cyan = '#4DEBFF'
        white = '#EAF6FF'
        brightBlack = '#5B6F8E'
        brightRed = '#FF8BAC'
        brightGreen = '#8CFFD5'
        brightYellow = '#FFE8A3'
        brightBlue = '#A9C7FF'
        brightPurple = '#D5BCFF'
        brightCyan = '#A3F6FF'
        brightWhite = '#FFFFFF'
    }
    Add-Or-Replace-Scheme -Settings $settings -Scheme $scheme

    $terminalTheme = [pscustomobject]@{
        name = 'CleanGlass'
        tab = [pscustomobject]@{
            background = '#070B16'
            unfocusedBackground = '#050812'
            showCloseButton = 'activeOnly'
        }
        tabRow = [pscustomobject]@{
            background = '#030610'
            unfocusedBackground = '#030610'
        }
        window = [pscustomobject]@{
            applicationTheme = 'dark'
        }
    }
    if (-not $settings.PSObject.Properties['themes'] -or -not $settings.themes) {
        $settings | Add-Member -NotePropertyName themes -NotePropertyValue @() -Force
    }
    $settings.themes = @($settings.themes | Where-Object { $_.name -notin @('PrismGlass','CleanGlass') })
    $settings.themes += $terminalTheme

    $defaults = $settings.profiles.defaults
    $defaults | Add-Member -NotePropertyName colorScheme -NotePropertyValue 'CleanGlass 2026' -Force
    $defaults | Add-Member -NotePropertyName font -NotePropertyValue ([pscustomobject]@{ face = 'FiraCode Nerd Font'; size = 11.5; weight = 'medium' }) -Force
    $defaults | Add-Member -NotePropertyName opacity -NotePropertyValue 84 -Force
    $defaults | Add-Member -NotePropertyName useAcrylic -NotePropertyValue $true -Force
    $defaults.PSObject.Properties.Remove('backgroundImage')
    $defaults.PSObject.Properties.Remove('backgroundImageOpacity')
    $defaults.PSObject.Properties.Remove('backgroundImageStretchMode')
    $defaults.PSObject.Properties.Remove('backgroundImageAlignment')
    $defaults | Add-Member -NotePropertyName cursorShape -NotePropertyValue 'filledBox' -Force
    $defaults | Add-Member -NotePropertyName padding -NotePropertyValue '14, 10, 14, 10' -Force
    $defaults | Add-Member -NotePropertyName historySize -NotePropertyValue 20000 -Force

    $settings | Add-Member -NotePropertyName theme -NotePropertyValue 'CleanGlass' -Force
    $settings | Add-Member -NotePropertyName copyOnSelect -NotePropertyValue $false -Force
    $settings | Add-Member -NotePropertyName copyFormatting -NotePropertyValue 'none' -Force
    $settings | Add-Member -NotePropertyName trimBlockSelection -NotePropertyValue $true -Force
    $settings | Add-Member -NotePropertyName snapToGridOnResize -NotePropertyValue $true -Force
    $settings | Add-Member -NotePropertyName useAcrylicInTabRow -NotePropertyValue $true -Force

    $pwshGuid = '{574e775e-4f2a-5b96-ac1e-a2962a402336}'
    $settings | Add-Member -NotePropertyName defaultProfile -NotePropertyValue $pwshGuid -Force

    $cmdProfile = [pscustomobject]@{
        guid = '{0caa0dad-35be-5f56-a8ff-afceeeaa6101}'
        name = 'Command Prompt'
        commandline = '%SystemRoot%\System32\cmd.exe'
        hidden = $false
    }
    Add-Or-Replace-Profile -Settings $settings -Profile $cmdProfile

    $gitBash = Join-Path $env:ProgramFiles 'Git\bin\bash.exe'
    if (Test-Path -LiteralPath $gitBash) {
        $gitProfile = [pscustomobject]@{
            guid = '{2ece5bfe-50ed-5f3a-ab87-5cd4baafed2b}'
            name = 'Git Bash'
            commandline = "`"$gitBash`" --login -i"
            icon = Join-Path $env:ProgramFiles 'Git\mingw64\share\git\git-for-windows.ico'
            startingDirectory = '%USERPROFILE%'
            hidden = $false
        }
        Add-Or-Replace-Profile -Settings $settings -Profile $gitProfile
    }

    Add-Or-Replace-Keybinding -Settings $settings -Keys 'alt+shift+minus' -Command ([pscustomobject]@{ action = 'splitPane'; split = 'horizontal'; splitMode = 'duplicate' })
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'alt+shift+plus' -Command ([pscustomobject]@{ action = 'splitPane'; split = 'vertical'; splitMode = 'duplicate' })
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'ctrl+shift+d' -Command 'duplicateTab'
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'ctrl+shift+w' -Command 'closePane'
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'alt+left' -Command ([pscustomobject]@{ action = 'moveFocus'; direction = 'left' })
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'alt+right' -Command ([pscustomobject]@{ action = 'moveFocus'; direction = 'right' })
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'alt+up' -Command ([pscustomobject]@{ action = 'moveFocus'; direction = 'up' })
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'alt+down' -Command ([pscustomobject]@{ action = 'moveFocus'; direction = 'down' })
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'ctrl+shift+p' -Command 'commandPalette'
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'ctrl+shift+f' -Command 'find'
    Add-Or-Replace-Keybinding -Settings $settings -Keys 'ctrl+shift+t' -Command 'newTab'

    $settings | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $SettingsPath -Encoding utf8
    $Changed.Add("Updated Windows Terminal settings: $SettingsPath")
}

function Configure-GitDelta {
    if (-not (Get-CommandPath 'delta')) {
        $Warnings.Add('delta is not currently resolvable; Git pager configuration skipped')
        return
    }
    git config --global core.pager 'delta'
    git config --global interactive.diffFilter 'delta --color-only'
    git config --global delta.navigate true
    git config --global delta.side-by-side true
    git config --global delta.line-numbers true
    git config --global delta.syntax-theme 'Visual Studio Dark+'
    git config --global merge.conflictStyle zdiff3
    $Changed.Add('Configured Git to use delta for diff/log paging without changing Git identity')
}

function Validate-Environment {
    $commands = 'pwsh','git','oh-my-posh','rg','fd','bat','jq','delta','fzf','zoxide','lazygit','gh'
    foreach ($command in $commands) {
        $path = Get-CommandPath $command
        if ($path) {
            $Changed.Add("Validated command: $command -> $path")
        } else {
            $Warnings.Add("Validation missing command: $command")
        }
    }

    try {
        $profilePath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PowerShell\Microsoft.PowerShell_profile.ps1'
        $elapsed = Measure-Command { pwsh -NoLogo -NoProfile -Command ". '$profilePath'; 'profile-ok'" | Out-Null }
        $Changed.Add("PowerShell profile load check completed in $([math]::Round($elapsed.TotalMilliseconds)) ms")
    } catch {
        $Warnings.Add("PowerShell profile validation failed: $($_.Exception.Message)")
    }
}

function Write-Report {
    param([string]$SettingsPath, [string]$ProfilePath)
    Ensure-Dir $ReportRoot
    $backupText = if ($Backups.Count) {
        ($Backups | ForEach-Object { "- $($_.OriginalPath) -> $($_.BackupPath)" }) -join "`n"
    } else {
        '- No existing config files needed backup.'
    }
    $installedText = if ($Installed.Count) { ($Installed | ForEach-Object { "- $_" }) -join "`n" } else { '- Nothing new installed.' }
    $skippedText = if ($Skipped.Count) { ($Skipped | ForEach-Object { "- $_" }) -join "`n" } else { '- Nothing skipped.' }
    $changedText = if ($Changed.Count) { ($Changed | ForEach-Object { "- $_" }) -join "`n" } else { '- No changes recorded.' }
    $warningText = if ($Warnings.Count) { ($Warnings | ForEach-Object { "- $_" }) -join "`n" } else { '- No warnings.' }

    $report = @"
# Terminal Setup Report

Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')

## Prompt Choice

Primary prompt: Oh My Posh.

Reason: Oh My Posh is already installed, has strong Windows Terminal integration, and gives the futuristic segmented prompt requested without adding a second prompt framework to maintain.

## Installed

$installedText

## Already Present or Skipped

$skippedText

## Changed

$changedText

## Backups

Backup folder: $BackupDir

$backupText

Rollback manifest: $ManifestPath

## Main Files

- Setup script: C:\ai-agent-tools\scripts\setup-beautiful-terminal.ps1
- Rollback script: C:\ai-agent-tools\scripts\rollback-terminal-setup.ps1
- PowerShell profile: $ProfilePath
- Windows Terminal settings: $SettingsPath
- Oh My Posh theme: $ThemePath

## Warnings

$warningText

## Manual Validation Commands

~~~powershell
pwsh -NoLogo
`$PROFILE
Get-Command pwsh, git, oh-my-posh, rg, fd, bat, jq, delta, fzf, zoxide
Measure-Command { pwsh -NoLogo -NoProfile -Command ". '`$PROFILE'" }
git config --global --get core.pager
~~~

## Rollback

Run:

~~~powershell
pwsh -ExecutionPolicy Bypass -File C:\ai-agent-tools\scripts\rollback-terminal-setup.ps1
~~~

By default, the rollback script restores the newest backup under C:\ai-agent-tools\terminal-backups.

## Next Recommended Upgrades

- Install WSL distributions only when you explicitly want them; no WSL distro was installed by this setup.
- Consider adding repo-specific `.editorconfig` and Git hooks per project rather than globally.
- Keep PowerShell, Windows Terminal, Git, Oh My Posh, and CLI tools updated through winget.
"@
    $report | Set-Content -LiteralPath $ReportPath -Encoding utf8
}

Write-Step 'Phase 1 - Audit'
Ensure-Dir $BackupRoot
Ensure-Dir $ScriptRoot
Ensure-Dir $ReportRoot
Ensure-Dir $TerminalRoot

$settingsPath = Get-WindowsTerminalSettingsPath
$profilePath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PowerShell\Microsoft.PowerShell_profile.ps1'
$gitConfigPath = Join-Path $env:USERPROFILE '.gitconfig'

Write-Host "Windows: $((Get-ComputerInfo | Select-Object -ExpandProperty WindowsProductName))"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
Write-Host "Windows Terminal settings: $settingsPath"
Write-Host "PowerShell profile: $profilePath"
Write-Host 'Planned changes: backup Terminal settings/Git config/profile if present, install missing QoL tools, write Oh My Posh theme, update profile, tune Windows Terminal, configure delta if installed.'

Write-Step 'Phase 2 - Backup'
Backup-File -Path $settingsPath -Label 'windows-terminal-settings.json'
Backup-File -Path $profilePath -Label 'Microsoft.PowerShell_profile.ps1'
Backup-File -Path $gitConfigPath -Label '.gitconfig'

$Backups | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ManifestPath -Encoding utf8

Write-Step 'Phase 3 - Install/Update'
Update-SessionPath
Install-WingetPackage -CommandName 'pwsh' -PackageId 'Microsoft.PowerShell' -DisplayName 'PowerShell 7'
Install-WingetPackage -CommandName 'wt' -PackageId 'Microsoft.WindowsTerminal' -DisplayName 'Windows Terminal'
Install-WingetPackage -CommandName 'git' -PackageId 'Git.Git' -DisplayName 'Git'
Install-WingetPackage -CommandName 'oh-my-posh' -PackageId 'JanDeDobbeleer.OhMyPosh' -DisplayName 'Oh My Posh'
Install-WingetPackage -CommandName 'rg' -PackageId 'BurntSushi.ripgrep.MSVC' -DisplayName 'ripgrep'
Install-WingetPackage -CommandName 'fd' -PackageId 'sharkdp.fd' -DisplayName 'fd'
Install-WingetPackage -CommandName 'bat' -PackageId 'sharkdp.bat' -DisplayName 'bat'
Install-WingetPackage -CommandName 'jq' -PackageId 'jqlang.jq' -DisplayName 'jq'
Install-WingetPackage -CommandName 'delta' -PackageId 'dandavison.delta' -DisplayName 'delta'
Install-WingetPackage -CommandName 'fzf' -PackageId 'junegunn.fzf' -DisplayName 'fzf'
Install-WingetPackage -CommandName 'zoxide' -PackageId 'ajeetdsouza.zoxide' -DisplayName 'zoxide'
Install-WingetPackage -CommandName 'lazygit' -PackageId 'JesseDuffield.lazygit' -DisplayName 'lazygit'
Install-WingetPackage -CommandName 'gh' -PackageId 'GitHub.cli' -DisplayName 'GitHub CLI'
Install-WingetPackage -CommandName 'eza' -PackageId 'eza-community.eza' -DisplayName 'eza'
Install-ModuleIfMissing -Name 'Terminal-Icons'
Update-SessionPath

Write-Step 'Phase 4 - Configure'
Write-OhMyPoshTheme
Write-PowerShellProfile -ProfilePath $profilePath
Configure-WindowsTerminal -SettingsPath $settingsPath
Configure-GitDelta

Write-Step 'Phase 5 - Validate'
Validate-Environment

Write-Step 'Phase 6 - Report'
Write-Report -SettingsPath $settingsPath -ProfilePath $profilePath
Write-Host "Report written to $ReportPath" -ForegroundColor Green
