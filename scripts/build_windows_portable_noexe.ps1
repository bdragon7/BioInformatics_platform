$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (Test-Path BioinformaticsStudio-windows-noexe) { Remove-Item -Recurse -Force BioinformaticsStudio-windows-noexe }
if (Test-Path BioinformaticsStudio-windows-noexe.zip) { Remove-Item -Force BioinformaticsStudio-windows-noexe.zip }

New-Item -ItemType Directory -Path BioinformaticsStudio-windows-noexe | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio-windows-noexe/config | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio-windows-noexe/projects | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio-windows-noexe/plugins | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio-windows-noexe/templates | Out-Null

Copy-Item src BioinformaticsStudio-windows-noexe/src -Recurse -Force
Copy-Item tests BioinformaticsStudio-windows-noexe/tests -Recurse -Force
Copy-Item main.py BioinformaticsStudio-windows-noexe/main.py -Force
Copy-Item pyproject.toml BioinformaticsStudio-windows-noexe/pyproject.toml -Force
Copy-Item README.md BioinformaticsStudio-windows-noexe/README.md -Force
Copy-Item launch_bioinfostudio.bat BioinformaticsStudio-windows-noexe/launch_bioinfostudio.bat -Force
Copy-Item launch_bioinfostudio.cmd BioinformaticsStudio-windows-noexe/launch_bioinfostudio.cmd -Force
Copy-Item launch_conda.bat BioinformaticsStudio-windows-noexe/launch_conda.bat -Force
Copy-Item launch_spyder.bat BioinformaticsStudio-windows-noexe/launch_spyder.bat -Force
Copy-Item scripts/setup_conda_env.bat BioinformaticsStudio-windows-noexe/setup_conda_env.bat -Force
Copy-Item scripts/setup_spyder_env.bat BioinformaticsStudio-windows-noexe/setup_spyder_env.bat -Force

$launcher = @'
@echo off
REM Script-based launcher (no .exe build required)
cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\src

if exist "%CD%\.venv\Scripts\python.exe" (
  "%CD%\.venv\Scripts\python.exe" main.py %*
  goto :end
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 main.py %*
  goto :end
)

where python >nul 2>nul
if %errorlevel%==0 (
  python main.py %*
  goto :end
)

echo Python 3.11+ not found. Install Python or use embedded python folder.
pause
:end
'@
Set-Content -Path BioinformaticsStudio-windows-noexe/run_windows_noexe.bat -Value $launcher -Encoding ascii

$bootstrap = @'
@echo off
cd /d "%~dp0"
py -3.11 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[gui]"
if not "%BIOPLATFORM_AUTOLOAD_PYMOL%"=="0" (
  python -m pip install "git+https://github.com/schrodinger/pymol-open-source.git"
)
echo Environment ready. Use run_windows_noexe.bat to start.
pause
'@
Set-Content -Path BioinformaticsStudio-windows-noexe/setup_windows_env.bat -Value $bootstrap -Encoding ascii

Compress-Archive -Path BioinformaticsStudio-windows-noexe/* -DestinationPath BioinformaticsStudio-windows-noexe.zip -Force
Write-Host "Built BioinformaticsStudio-windows-noexe.zip"
