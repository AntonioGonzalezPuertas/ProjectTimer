@echo off
echo Running Project Timer with console output visible...
echo.
cd /d "%~dp0"
python project_timer.py
echo.
echo Press any key to close...
pause >nul