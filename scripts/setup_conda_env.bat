@echo off
setlocal
set ENV_NAME=%1
if "%ENV_NAME%"=="" set ENV_NAME=bioinfostudio

cd /d "%~dp0\.."

where conda >nul 2>nul
if errorlevel 1 (
  echo Conda not found. Install Miniconda/Anaconda first.
  pause
  exit /b 1
)

call conda env list | findstr /r /c:"^%ENV_NAME% " >nul
if errorlevel 1 (
  call conda create -y -n %ENV_NAME% python=3.11
)

call conda activate %ENV_NAME%
python -m pip install --upgrade pip
python -m pip install -e .[gui]

echo Conda environment ready: %ENV_NAME%
echo Launch with: launch_conda.bat %ENV_NAME%
pause
endlocal
