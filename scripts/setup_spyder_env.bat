@echo off
setlocal
cd /d "%~dp0\.."

where python >nul 2>nul
if errorlevel 1 (
  echo Python not found on PATH. Install Python 3.11+ first.
  pause
  exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -e .[gui]

echo Spyder-compatible environment is ready (using current Python interpreter).
echo If Spyder uses a different interpreter, set it in Spyder:
echo Tools ^> Preferences ^> Python interpreter.
pause
endlocal
