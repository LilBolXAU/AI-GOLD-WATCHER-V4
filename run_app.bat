@echo off
title AI GOLD WATCHER V4 - DESKTOP APPLICATION
echo ========================================================
echo   AI GOLD WATCHER V4 — KHOI DONG GIAO DIEN DESKTOP
echo ========================================================
echo Dang ket noi giao dien CustomTkinter...
python src/ui/desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co loi khi khoi dong giao dien.
    pause
)
