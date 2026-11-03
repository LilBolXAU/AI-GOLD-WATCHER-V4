# WINDOWS 11 & METATRADER 5 SETUP GUIDE — AI GOLD WATCHER V4

## 1. System Requirements & Prerequisites
- **Operating System**: Windows 11 x86-64 (Build 22000+)
- **Python**: Python 3.13.7 64-bit (`python.exe` must be in system PATH)
- **Terminal**: Exness MetaTrader 5 (MT5 build 4000+)
- **Trading Account**: Exness Standard Demo Account (Leverage 1:2000 recommended on demo for margin headroom; volume strictly quantized to 0.01 lot)

---

## 2. Python Environment Setup
1. Verify Python version and architecture:
   ```powershell
   python --version
   python -c "import struct; print('64-bit' if struct.calcsize('P') * 8 == 64 else '32-bit')"
   ```
   *Expected output*: `Python 3.13.7` and `64-bit`.

2. Install or verify required packages:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

---

## 3. MetaTrader 5 Terminal Configuration (Exness)
1. In MetaTrader 5, open **Tools -> Options -> Expert Advisors**:
   - Enable **Allow algorithmic trading**.
   - Keep WebRequest settings secured.
2. In **Market Watch**, right click and select **Symbols**:
   - Locate and enable `XAUUSDm` (under `Forex_Standard` or `Metals_Standard`).
   - Confirm symbol parameters:
     - Contract Size: `100.0`
     - Digits: `2`
     - Minimum Volume: `0.01`
     - Volume Step: `0.01`
3. Optional `.env` configuration:
   - Copy `.env.example` to `.env`:
     ```powershell
     Copy-Item .env.example .env
     ```
   - If connecting to an external terminal instance, specify:
     ```ini
     MT5_PATH="C:\Program Files\MetaTrader 5\terminal64.exe"
     MT5_SERVER="Exness-MT5Real"
     MT5_LOGIN=12345678
     ```
   - Note: If MT5 is already running on desktop, Python's `MetaTrader5` package automatically attaches to the active desktop session without credentials.

---

## 4. Verification & Health Audit
Execute the system diagnostic check:
```powershell
.\diagnose.bat
```
This verifies:
1. Pydantic configuration and safety latches (`DRY_RUN_ENABLED=True`).
2. SQLite storage initialization at `data/v4_trading.db`.
3. Causal indicator calculations on closed bars.
4. Regime detection and hysteresis state.
5. Pre-trade risk veto gate.
