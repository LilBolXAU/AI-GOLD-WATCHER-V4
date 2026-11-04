@echo off
title AI GOLD WATCHER V4 - AUTO UPDATER AND LAUNCHER
echo ========================================================
echo   AI GOLD WATCHER V4 - AUTO SYNC AND LAUNCHER
echo ========================================================
echo [1/3] Kiem tra va dong bo ban cap nhat moi nhat...
if not exist ".git" (
    echo [THONG BAO] Thu muc dang khoi tao ket noi Git voi GitHub...
    git init >nul 2>&1
    git remote add origin https://github.com/LilBolXAU/AI-GOLD-WATCHER-V4.git >nul 2>&1
    git fetch origin main >nul 2>&1
    git checkout -f -B main origin/main >nul 2>&1
)

git pull origin main >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Da dong bo ma nguon moi nhat tu GitHub thanh cong!
) else (
    echo [THONG BAO] Dang su dung phien ban hien tai (ung dung co co che tu dong cap nhat truc tiep).
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
