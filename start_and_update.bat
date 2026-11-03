@echo off
title AI GOLD WATCHER V4 - AUTO UPDATER AND LAUNCHER
echo ========================================================
echo   AI GOLD WATCHER V4 - AUTO SYNC AND LAUNCHER
echo ========================================================
echo [1/3] Kiem tra va tai ban cap nhat moi nhat tu GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [CANH BAO] Khong the tai ban cap nhat tu GitHub.
    echo He thong se tiep tuc chay voi phien ban hien tai tren may.
) else (
    echo [OK] Da dong bo ma nguon moi nhat thanh cong!
)
echo.

echo [2/3] Kiem tra thu vien phan mem can thiet...
python -c "import customtkinter, pandas, MetaTrader5" >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :START_APP

echo [THONG BAO] Dang tu dong cai dat thu vien giao dien va MT5...
python -m pip install -r requirements.txt

:START_APP
echo [3/3] Khoi dong AI Gold Watcher V4 Desktop App...
python src/ui/desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co loi khi khoi dong giao dien.
    pause
)
