@echo off
title AI GOLD WATCHER V4 - DESKTOP APPLICATION
echo ========================================================
echo   AI GOLD WATCHER V4 - KHOI DONG GIAO DIEN DESKTOP
echo ========================================================

:: Kiem tra xem may da cai cac thu vien can thiet chua (customtkinter, pandas, MetaTrader5)
python -c "import customtkinter, pandas, MetaTrader5" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [THONG BAO] Phat hien may moi chua cai du thu vien can thiet!
    echo Dang tu dong cai dat: customtkinter, MetaTrader5, pandas, requests...
    echo Vui long cho trong giay lat (chi can cai 1 lan dau tien)...
    echo.
    python -m pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [CANH BAO] Cai dat thu vien gap loi. Vui long kiem tra ket noi Internet hoac Python tren may!
        pause
        exit /b 1
    )
    echo.
    echo [THANH CONG] Da cai dat xong tat ca thu vien!
    echo.
)

echo Dang ket noi giao dien CustomTkinter...
python src/ui/desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CANH BAO] Co loi khi khoi dong giao dien.
    pause
)
