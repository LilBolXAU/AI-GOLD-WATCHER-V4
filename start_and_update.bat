@echo off
title AI GOLD WATCHER V4 - AUTO UPDATER & LAUNCHER
echo ========================================================
echo   AI GOLD WATCHER V4 - AUTO SYNC & LAUNCHER
echo ========================================================
echo [1/2] Kiem tra va tai ban cap nhat moi nhat tu GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [CANH BAO] Khong the tai ban cap nhat (co the do mat mang hoac chua ket noi GitHub).
    echo He thong se tiep tuc chay voi phien ban hien tai tren may.
) else (
    echo [OK] Da dong bo ma nguon moi nhat thanh cong!
)
echo.

echo [2/2] Khoi dong AI Gold Watcher V4 Desktop App...
python src/ui/desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co loi khi khoi dong giao dien.
    pause
)
