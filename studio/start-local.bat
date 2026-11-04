@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3.12 -c "import sys" >nul 2>nul
if errorlevel 1 goto usepython
py -3.12 backend\start_studio.py
goto done
:usepython
python backend\start_studio.py
:done
if errorlevel 1 pause
