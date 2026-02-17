@echo off
REM Launch Bioinformatics Studio
cd /d "%~dp0"
set PYTHONPATH=%CD%;%CD%\src
if exist "%CD%\python\python.exe" (
  set PY_EXE=%CD%\python\python.exe
) else (
  set PY_EXE=python
)

REM Portable dependency guard for local Gemma inference.
%PY_EXE% -c "import llama_cpp" >nul 2>nul
if errorlevel 1 (
  echo [BioInfoStudio] llama-cpp-python not found in portable runtime.
  echo [BioInfoStudio] Local Gemma will run in fallback mode until dependency is installed.
)

%PY_EXE% main.py %*
if errorlevel 1 pause
