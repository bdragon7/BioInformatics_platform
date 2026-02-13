@echo off
REM Launch Bioinformatics Studio
cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\src
if exist "%CD%\python\python.exe" (
  "%CD%\python\python.exe" main.py %*
) else (
  python main.py %*
)
if errorlevel 1 pause
