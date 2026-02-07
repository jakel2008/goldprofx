@echo off
setlocal
cd /d "D:\GOLD PRO" || exit /b 1

REM Kill anything listening on port 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr LISTENING') do (
  echo Stopping PID %%a on port 5000...
  taskkill /PID %%a /F >nul 2>nul
)

echo Starting web_app_complete.py...
start "GOLDPRO-WEB" /D "D:\GOLD PRO" "D:\GOLD PRO\.venv-1\Scripts\python.exe" "D:\GOLD PRO\web_app_complete.py"

timeout /t 2 >nul

where curl >nul 2>nul
if errorlevel 1 (
  echo curl not found; skipping HTTP probe.
  exit /b 0
)

echo Probing endpoints...
curl -I -s -o nul -w "plans:%%{http_code}^\n" http://127.0.0.1:5000/plans
curl -I -s -o nul -w "api_user:%%{http_code}^\n" http://127.0.0.1:5000/api/user

endlocal
