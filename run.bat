@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 (
    echo Error: Python 3.10+ not found. Install from https://www.python.org/downloads/
    echo Enable "Add python.exe to PATH" during installation.
    exit /b 1
  )
  echo Installing dependencies...
  call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" main.py
exit /b %ERRORLEVEL%
