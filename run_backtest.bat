@echo off
echo ===================================================
echo   Running AI GOLD WATCHER V4 Event-Driven Backtest
echo ===================================================
python src/main.py --mode backtest --bars 500 --output reports/backtest_tearsheet.md
pause
