@echo off
setlocal
cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\src

where spyder >nul 2>nul
if errorlevel 1 (
  echo Spyder not found on PATH.
  echo Open Spyder manually and run main.py from this folder.
  pause
  exit /b 1
)

REM Open project script in Spyder (works well on corporate-managed laptops)
spyder main.py
endlocal
