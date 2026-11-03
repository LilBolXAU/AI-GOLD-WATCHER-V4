@echo off
title AI GOLD WATCHER V4 - PUSH UPDATE TO GITHUB
echo ========================================================
echo   AI GOLD WATCHER V4 - DONG BO CAP NHAT LEN GITHUB
echo ========================================================
echo.
set /p commit_msg="Nhap mo ta ban cap nhat (vi du: 'Toi uu Win Rate 80%'): "
if "%commit_msg%"=="" set commit_msg=Cap nhat ma nguon moi nhat

echo.
echo [1/3] Dang chuan bi tep...
git add .
echo.
echo [2/3] Dang ghi nhan ban cap nhat: "%commit_msg%"...
git commit -m "%commit_msg%"
echo.
echo [3/3] Dang day code len GitHub...
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [THANH CONG] Ban cap nhat da duoc day len GitHub!
    echo   May cua ban ban chi can chay "start_and_update.bat"
    echo   la se tu dong nhan duoc ban moi nhat nay ngay lap tuc!
    echo ========================================================
) else (
    echo.
    echo [THAT BAI] Khong the day code len GitHub. Vui long kiem tra ket noi mang hoac tai khoan.
)
echo.
pause
