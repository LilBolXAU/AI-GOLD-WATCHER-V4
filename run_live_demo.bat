@echo off
echo ========================================================
echo   AI GOLD WATCHER V4 — REAL-TIME LIVE DEMO TRADING
echo ========================================================
echo  [SECURITY NOTICE]:
echo  - Strictly restricted to MetaTrader 5 DEMO accounts only.
echo  - Volume: Lot dong theo ATR va Von (Min 0.01 lot)
echo  - Risk Budget: 4.0%% von / lenh
echo  - Target Profit: 6.0%% von / lenh (R:R 1:1.5)
echo  - Scalping Protection: Auto Break-Even va Dynamic Trailing Stop
echo  - Max Concurrent Positions: 1 (Khong nhoi, khong Martingale)
echo  - Circuit Breakers: Active (-8.0%% von ngay)
echo ========================================================
python src/main.py --mode live-demo --poll-interval 5.0
pause
