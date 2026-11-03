@echo off
title AI GOLD WATCHER V4 - DESKTOP APPLICATION
echo ========================================================
echo   AI GOLD WATCHER V4 - KHOI DONG GIAO DIEN DESKTOP
echo ========================================================

:: Kiem tra xem may da cai cac thu vien can thiet chua
python -c "import customtkinter, pandas, MetaTrader5" >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :LAUNCH

echo [THONG BAO] Phat hien may chua cai dat du thu vien can thiet!
echo Dang tu dong cai dat customtkinter, MetaTrader5, pandas, requests...
echo Vui long cho trong giay lat...
echo.
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Cai dat thu vien gap loi. Vui long kiem tra ket noi Internet!
    pause
    exit /b 1
)
echo.
echo [THANH CONG] Da cai dat xong tat ca thu vien!
echo.

:LAUNCH
echo Dang ket noi giao dien CustomTkinter...
python src/ui/desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co loi khi khoi dong giao dien.
    pause
)
