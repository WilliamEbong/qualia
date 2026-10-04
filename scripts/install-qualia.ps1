# One-time Qualia setup for Windows: run by double-clicking "Install Qualia.cmd" in the Qualia folder.
# Installs missing tools, Qualia itself and the demo, adds Desktop/Start-menu shortcuts, then opens Qualia.
# Safe to run again (for example after downloading a newer version).

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Step($number, $text) { Write-Host ''; Write-Host "[$number/6] $text" -ForegroundColor Cyan }
function Run($exe) {
    & $exe @args
    if ($LASTEXITCODE -ne 0) { throw "'$exe $args' did not finish successfully (exit code $LASTEXITCODE)." }
}
function Have($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

try {
    Write-Host 'Setting up Qualia. This takes a few minutes the first time; later runs are quicker.'

    Step 1 'Checking uv (the tool that installs Qualia and Python)'
    if (-not (Have 'uv')) {
        Write-Host 'Installing uv from astral.sh...'
        powershell -NoProfile -ExecutionPolicy Bypass -Command 'irm https://astral.sh/uv/install.ps1 | iex'
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
        if (-not (Have 'uv')) { throw 'uv could not be installed. Check your internet connection and run Install Qualia again.' }
    }
    Write-Host 'uv is ready.'

    Step 2 'Checking Git (Qualia uses it to keep each project''s history)'
    if (-not (Have 'git')) {
        if (-not (Have 'winget')) { throw 'Git is missing. Install it from https://git-scm.com/download/win, then run Install Qualia again.' }
        Write-Host 'Installing Git with winget. Windows may ask for permission.'
        Run winget install --id Git.Git --exact --source winget --accept-package-agreements --accept-source-agreements
        $env:Path = "$env:ProgramFiles\Git\cmd;$env:Path"
        if (-not (Have 'git')) { throw 'Git was installed but is not available yet. Restart your computer, then run Install Qualia again.' }
    }
    Write-Host 'Git is ready.'

    Step 3 'Installing Qualia and Python (only what Qualia needs to run)'
    Run uv sync --locked --no-dev --inexact

    Step 4 'Preparing the Qualia screens'
    if (-not (Test-Path 'web\dist\index.html')) {
        if (-not (Have 'npm')) { throw 'This copy of Qualia has no prebuilt screens. Download the Qualia zip from the GitHub Releases page instead.' }
        Run npm --prefix web ci
        Run npm --prefix web run build
    }
    Write-Host 'Screens are ready.'

    Step 5 'Adding the AnnoMI demonstration project'
    try {
        if (-not (Test-Path 'demo\data\AnnoMI-simple.csv')) { Run .venv\Scripts\python.exe scripts\fetch_demo.py }
        Run .venv\Scripts\qualia.exe demo | Out-Null
        Write-Host 'Demo project is ready.'
    } catch {
        Write-Warning "The demo could not be added ($($_.Exception.Message)). Qualia still works; run Install Qualia again later to add it."
    }

    Step 6 'Creating the Qualia shortcuts'
    $app = Join-Path $root '.venv\Scripts\qualia-app.exe'
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
        $shortcut = $shell.CreateShortcut((Join-Path $folder 'Qualia.lnk'))
        $shortcut.TargetPath = $app
        $shortcut.WorkingDirectory = $root
        $shortcut.IconLocation = (Join-Path $root 'web\public\qualia.ico')
        $shortcut.Description = 'Qualia - qualitative coding you can audit'
        $shortcut.Save()
    }
    Write-Host 'Added Qualia to your Desktop and Start menu.'

    Write-Host ''
    Write-Host 'All done. Qualia is opening now. Next time, double-click the Qualia icon.' -ForegroundColor Green
    Write-Host 'Closing the Qualia window stops Qualia. Your projects are stored in your Qualia folder in your user profile.'
    Start-Process $app
} catch {
    Write-Host ''
    Write-Host "Setup stopped: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Fix the problem above, then double-click Install Qualia again. Your research projects were not changed.'
    exit 1
}
