@echo off
title AI GOLD WATCHER V4 - AUTO UPDATER & LAUNCHER
echo ========================================================
echo   AI GOLD WATCHER V4 - AUTO SYNC & LAUNCHER
echo ========================================================
echo [1/3] Kiem tra va tai ban cap nhat moi nhat tu GitHub...
git pull origin main
if %ERRORLEVEL% NEQ 0 (
    echo [CANH BAO] Khong the tai ban cap nhat (co the do mat mang hoac chua ket noi GitHub).
    echo He thong se tiep tuc chay voi phien ban hien tai tren may.
) else (
    echo [OK] Da dong bo ma nguon moi nhat thanh cong!
)
echo.

echo [2/3] Kiem tra thu vien can thiet...
pip install -r requirements.txt --quiet
echo [OK] Thu vien da san sang.
echo.

echo [3/3] Khoi dong AI Gold Watcher V4...
echo Chon che do chay:
echo   1. Live Demo MT5 (Quet 5s/lan theo thoi gian thuc - Mac dinh)
echo   2. Paper Replay (Mo phong kiem thu 300 nen M5)
echo   3. Mo Web Dashboard truc quan
set /p mode_choice="Nhap lua chon [1, 2 hoac 3] (Nhan Enter de chay che do 1): "

if "%mode_choice%"=="2" (
    python src/main.py --mode paper --live --bars 300
) else if "%mode_choice%"=="3" (
    streamlit run src/monitoring/dashboard.py
) else (
    python src/main.py --mode live-demo --poll-interval 5.0
)

pause
