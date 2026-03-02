@echo off
setlocal
cd /d "D:\GOLD PRO"
if not exist "logs" mkdir "logs"
set "PYTHON_EXE=C:\Users\Discovery PC\AppData\Local\Programs\Python\Python313\python.exe"

:loop
echo [%date% %time%] Starting web_app_complete.py>>"logs\server_supervisor.log"
"%PYTHON_EXE%" "web_app_complete.py" >>"logs\server.out.log" 2>>"logs\server.err.log"
echo [%date% %time%] Process exited with code %errorlevel%. Restarting in 5s...>>"logs\server_supervisor.log"
timeout /t 5 /nobreak >nul
goto loop
