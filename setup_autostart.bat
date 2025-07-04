@echo off
echo Setting up HMS to start automatically...

:: Get the current directory
set "CURRENT_DIR=%~dp0"
set "BATCH_FILE=%CURRENT_DIR%start_hms.bat"

:: Create the scheduled task
schtasks /create /tn "HMS Startup" /tr "%BATCH_FILE%" /sc onstart /ru "%USERNAME%" /rl HIGHEST /f

echo.
echo HMS has been set up to start automatically when you log in.
echo You can verify this in Task Scheduler (taskschd.msc)
echo.
pause 