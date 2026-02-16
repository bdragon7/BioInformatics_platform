@echo off
setlocal
set ENV_NAME=%1
if "%ENV_NAME%"=="" set ENV_NAME=bioinfostudio

cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\src

where conda >nul 2>nul
if errorlevel 1 (
  echo Conda not found. Install Miniconda/Anaconda first.
  pause
  exit /b 1
)

call conda activate %ENV_NAME%
if errorlevel 1 (
  echo Failed to activate conda environment: %ENV_NAME%
  echo Run scripts\setup_conda_env.bat first.
  pause
  exit /b 1
)

python main.py %2 %3 %4 %5 %6 %7 %8 %9
endlocal
