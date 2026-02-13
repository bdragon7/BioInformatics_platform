$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -e ".[gui]"

if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path BioinformaticsStudio) { Remove-Item -Recurse -Force BioinformaticsStudio }

pyinstaller --noconfirm --name BioinformaticsStudio --windowed main.py

New-Item -ItemType Directory -Path BioinformaticsStudio | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio/config | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio/projects | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio/plugins | Out-Null
New-Item -ItemType Directory -Path BioinformaticsStudio/templates | Out-Null

Copy-Item dist/BioinformaticsStudio/* BioinformaticsStudio/ -Recurse -Force
Copy-Item launch_bioinfostudio.bat BioinformaticsStudio/ -Force
Copy-Item launch_bioinfostudio.cmd BioinformaticsStudio/ -Force
Copy-Item README.md BioinformaticsStudio/ -Force

Compress-Archive -Path BioinformaticsStudio/* -DestinationPath BioinformaticsStudio-portable-windows.zip -Force
Write-Host "Built BioinformaticsStudio-portable-windows.zip"
