@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHON=python"

if exist "%ROOT%backend\venv\Scripts\python.exe" set "PYTHON=%ROOT%backend\venv\Scripts\python.exe"

curl.exe --silent --fail http://127.0.0.1:8000/health >nul 2>nul
if errorlevel 1 (
  echo Starting The Forwarded Seal API...
  start "The Forwarded Seal API" /D "%ROOT%backend" "%PYTHON%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) else (
  echo The Forwarded Seal API is already running.
)

echo Starting The Forwarded Seal frontend...
cd /d "%ROOT%"
npm.cmd run dev
