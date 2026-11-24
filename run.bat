@echo off
rem Double-click or run: finds Python and starts the actiontrack menu.
cd /d "%~dp0"
where py >nul 2>nul && (py -3 run.py %* & goto :done)
where python >nul 2>nul && (python run.py %* & goto :done)
echo Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ and run this file again.
:done
pause
