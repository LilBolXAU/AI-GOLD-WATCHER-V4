# BUGS AND FIXES LOG — AI GOLD WATCHER V4

**Document ID**: `AGW-V4-MEM-BUGS`  
**Classification**: Defect Tracking & Regression Ledger  
**Rule**: Every bug discovered during development, backtesting, or paper trading must be recorded with root cause, fix, and regression test link.  

---

## Active Defects (Open)
*None currently open.*

---

## Resolved Defects (Closed)

### BUG-001: Skill Discovery Depth Mismatch on Category Folders
- **Date Discovered**: 2026-11-03
- **Component**: Customization / Skill Discovery (`.agents/skills/`)
- **Symptom**: During initial skill installation from `ml4t-skills`, skills nested in subdirectories (`skills/data/build-bars/SKILL.md`) were not discovered by Antigravity's single-level scanner.
- **Root Cause**: Antigravity discovery searches only one level deep (`.agents/skills/<skill_name>/SKILL.md`). Nested category folders hid `SKILL.md` files from discovery.
- **Fix Applied**: Flattened the category hierarchy during installation, placing each skill directly into `.agents/skills/<name>/SKILL.md` (e.g. `.agents/skills/ml4t-stationarity-tests/SKILL.md`).
- **Regression Verification**: Ran verification script `Get-ChildItem -Directory` confirming all skills are discoverable at depth 1. Result: 100% discovery.

---

### BUG-002: Incomplete EMA Series Length Handling in check_ema_alignment
- **Date Discovered**: 2026-11-03
- **Severity**: High
- **Component**: `src/indicators/trend_indicators.py`
- **Symptom**: `MarketRegimeDetector` classified all trending datasets with length < 200 bars as `UNSTABLE` instead of `BULL_TRENDING` or `BEAR_TRENDING`.
- **Root Cause**: `calc_ema(series, 200)` explicitly returned all `np.nan` if `len(series) < 200`, causing `check_ema_alignment` comparison `ema_mid > ema_slow` to evaluate as False.
- **Fix Applied**: Removed artificial `len(series) < period` barrier in `calc_ema` (using pandas `ewm(adjust=False)` which works across any length), and allowed `check_ema_alignment` to rely on fast/mid alignment when slow is still warming up.
- **Regression Test**: `tests/unit/test_regime.py::test_regime_bull_trend_detection` and `test_regime_bear_trend_detection`.
- **Status**: RESOLVED

---

### BUG-003: Signal and Trade Repository Field Name Mismatches
- **Date Discovered**: 2026-11-03
- **Severity**: Medium
- **Component**: `src/storage/repositories.py`
- **Symptom**: AttributeError in `TradeRepository.save_closed_trade` and `SignalRepository.save_signal` (`sl_price` vs `stop_loss`, `tp_price` vs `take_profit`, missing `signal_id`).
- **Root Cause**: Repository SQL bindings referenced provisional variable names that did not match frozen dataclass field names in `ClosedTrade` and `SignalCandidate`.
- **Fix Applied**: Harmonized attribute accesses (`stop_loss`, `take_profit`, `points_pnl`), synthesized unique deterministic `signal_id`, and added `confidence_score` property on `ScoredSignal`.
- **Regression Test**: `tests/integration/test_pipeline.py::test_full_trading_pipeline`.
- **Status**: RESOLVED

---

### BUG-004: MT5 3-Digit Broker Gold Spread Unit Mismatch in Live Feed
- **Date Discovered**: 2026-11-03
- **Severity**: High
- **Component**: `src/data/mt5_client.py` (`LiveMT5Client.get_rates`)
- **Symptom**: Running `python src/main.py --mode paper --live --bars 300` resulted in `Total Trades: 0` despite valid setups being detected.
- **Root Cause**: Exness quotes Gold (`XAUUSDm`) with 3 digits (`point=0.001`), returning spread in raw broker ticks (e.g. 240 ticks = $0.24). The system's standard spread filter expects standard 0.01 USD cents (`max_spread_pts=35`). A spread of 240 caused `ConfidenceEngine` to assign 0 points for spread and veto all trades.
- **Fix Applied**: Added automatic broker point normalization in `LiveMT5Client.get_rates`: `spread_pts = int(round(raw_spread * broker_point / 0.01)) if broker_point < 0.01 else raw_spread`, normalizing 240 ticks down to 24 standard cents.
- **Regression Verification**: Re-ran live paper session over 300 bars: executed 2 paper trades (`BUY XAUUSDm`) with real SL/TP handling.
- **Status**: RESOLVED

---

### BUG-005: AttributeError on VirtualPosition.unrealized_pnl During Equity Snapshot
- **Date Discovered**: 2026-11-03
- **Severity**: Medium
- **Component**: `src/execution/virtual_position.py` / `src/main.py`
- **Symptom**: `AttributeError: 'VirtualPosition' object has no attribute 'unrealized_pnl'` when running paper session over 2000 bars with an active open position at a snapshot interval.
- **Root Cause**: `src/main.py` accessed `.unrealized_pnl` while `VirtualPosition` named the field `floating_pnl`.
- **Fix Applied**: Added `@property def unrealized_pnl(self) -> float: return self.floating_pnl` to `VirtualPosition`.
- **Regression Verification**: Re-ran `python src/main.py --mode paper --live --bars 2000`, completed 2000 bars without error, executed 4 trades, win rate 25%, final balance $47.56.
- **Status**: RESOLVED

---

### BUG-006: TelegramNotifier Disabled on Batch File Launch Due to Missing .env Load
- **Date Discovered**: 2026-11-03
- **Severity**: High
- **Component**: `src/monitoring/telegram_bot.py` / `src/main.py` / `run_live_demo.bat`
- **Symptom**: When launching `run_live_demo.bat`, log showed `Telegram Notifier: DISABLED (Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)` and bot did not reply to `/status`. Batch file also printed `'Von' is not recognized` due to unescaped `&`.
- **Root Cause**: `src/main.py` did not call `load_dotenv()`, so environment variables from `.env` were not inherited by the spawned Windows CMD process. Additionally, `&` in echo statements acted as command delimiters in Windows batch script.
- **Fix Applied**: Added `load_dotenv` in both `src/main.py` and `src/monitoring/telegram_bot.py` with direct fallback to parse `WORKSPACE_ROOT / ".env"`. Replaced `&` in `run_live_demo.bat` with `va`.
- **Regression Verification**: `TelegramNotifier` loads token and chat ID with `enabled=True` across all launch methods. Successfully processed user's pending `/status` command. All 70 tests pass.
- **Status**: RESOLVED

---

### BUG-007: Telegram Bot Update Contention on Multi-Client Token Reuse
- **Date Discovered**: 2026-11-03
- **Severity**: Medium
- **Component**: `src/monitoring/telegram_bot.py`
- **Symptom**: Telegram bot stopped replying to user commands (`/status`, `/balance`) when a second bot instance on a friend's machine was launched.
- **Root Cause**: Both hosts polled `getUpdates` with the same `TELEGRAM_BOT_TOKEN`. The friend's instance consumed incoming updates and rejected them because the user's chat ID was not in the friend's local `.env`.
- **Fix Applied**: Added multi-chat ID parsing support (`chat_id="id1, id2"`), targeted per-chat replies in `TelegramNotifier`, and documented dedicated bot token provisioning per user machine.
- **Status**: RESOLVED

---

### BUG-008: SQLite Database Malformed Disk Image on File Transfer
- **Date Discovered**: 2026-11-03
- **Severity**: High
- **Component**: `src/storage/database.py` (`Database`)
- **Symptom**: `sqlite3.DatabaseError: database disk image is malformed` crashed `run_live_demo_loop` at `equity_repo.record_snapshot` on friend's machine.
- **Root Cause**: The SQLite database file (`v4_trading.db`) in WAL mode was zipped/transferred while active or partially corrupted during cloud download.
- **Fix Applied**: Implemented `PRAGMA quick_check` at initialization and automated recovery (`_recover_corrupted_db`) in `Database._init_schema` which renames the corrupt file, cleans sidecars (`-wal`, `-shm`), and recreates a fresh schema automatically. Wrapped `get_connection` in exception handling to ensure connection handles close before raising.
- **Regression Verification**: Verified automated recovery via unit test injecting corrupted byte payload; all 79 pytest tests pass.
- **Status**: RESOLVED

---

### BUG-009: Volume Safety Cap Rejection & Silent Execution Failures on Large Balances
- **Date Discovered**: 2026-11-04
- **Severity**: Critical
- **Component**: `src/execution/mt5_order_bridge.py` (`MT5OrderBridge`), `src/main.py` (`run_live_demo_loop`)
- **Symptom**: Signals appeared with high AI probability, but no orders were executed in MT5 on client machine ($200.00 balance) while working fine on Admin machine ($50.81 balance).
- **Root Cause**:
  1. `mt5_order_bridge.py:144` contained an obsolete hardcoded volume safety cap `if order.volume > 0.01: return ExecutionResult(...)`. On $200+ balances, dynamic 4% risk calculated volume = 0.02 lot (or higher), which was hard rejected.
  2. `main.py:705` had no `else:` branch after `exec_res = bridge.send_market_order(...)`, causing order rejections to be completely silent with zero logs in GUI or Telegram.
  3. Client accounts with non-standard gold symbols (`XAUUSD` instead of `XAUUSDm`) failed `symbol_info` lookup.
  4. Disabled MT5 "Algo Trading" button caused retcode 10027 (`TRADE_RETCODE_CLIENT_DISABLES_AT`).
- **Fix Applied**:
  1. Replaced hardcoded 0.01 cap with dynamic broker step-rounding and a 5.0 lots safety cap.
  2. Added explicit `else:` error branch in `main.py` logging retcodes to GUI and dispatching Telegram alerts.
  3. Auto-resolved symbols across `XAUUSDm`, `XAUUSD`, `GOLD`, etc.
  4. Added `terminal_info().trade_allowed` pre-flight check alerting users to enable Algo Trading on MT5.
  5. Implemented direct GitHub ZIP fallback updater when Git is not installed.
- **Regression Verification**: `tests/unit/test_mt5_bridge.py:test_volume_cap_enforced` and `test_algo_trading_disabled_rejected`; all 112 pytest tests pass.
- **Status**: RESOLVED

---

## Defect Log Template (For Future Bugs)

```markdown
### BUG-XXX: [Brief Title]
- **Date Discovered**: YYYY-MM-DD
- **Severity**: [Critical | High | Medium | Low]
- **Component**: [Module ID & file path]
- **Symptom**: [Observed failure behavior]
- **Root Cause**: [Underlying bug analysis]
- **Fix Applied**: [Exact code change description]
- **Regression Test**: [Path to test in tests/ verifying the fix]
- **Status**: [RESOLVED | INVESTIGATING]
```
