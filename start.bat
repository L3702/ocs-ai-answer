@echo off
title OCS AI Server
cd /d "%~dp0"
python server.py
if errorlevel 1 (
    echo.
    echo [ERROR] Server crashed. Check the error above.
    pause
)
