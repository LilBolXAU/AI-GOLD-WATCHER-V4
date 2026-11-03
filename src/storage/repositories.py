"""
Data access repositories for AI GOLD WATCHER V4 SQLite storage.
"""

from typing import List, Optional
import pandas as pd
from src.storage.database import Database
from src.execution.trade_lifecycle import ClosedTrade
from src.scoring.signal_quality import ScoredSignal
from src.regime.regime_detector import MarketRegimeState


class TradeRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_closed_trade(self, trade: ClosedTrade) -> None:
        sql = """
        INSERT OR REPLACE INTO paper_trades (
            trade_id, symbol, side, volume, entry_price, entry_time,
            exit_price, exit_time, sl_price, tp_price, gross_pnl,
            spread_cost, slippage_cost, swap_cost, net_pnl, pnl_points,
            exit_reason, strategy_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    sql,
                    (
                        trade.trade_id,
                        trade.symbol,
                        trade.side.value,
                        trade.volume,
                        trade.entry_price,
                        trade.entry_time.isoformat(),
                        trade.exit_price,
                        trade.exit_time.isoformat(),
                        trade.stop_loss,
                        trade.take_profit,
                        trade.gross_pnl,
                        trade.spread_cost,
                        trade.slippage_cost,
                        0.0,
                        trade.net_pnl,
                        float(trade.points_pnl),
                        trade.exit_reason.value,
                        trade.strategy_id,
                    ),
                )
        finally:
            conn.close()

    def get_all_trades(self) -> List[dict]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM paper_trades ORDER BY exit_time ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


class SignalRepository:
    def __init__(self, db: Database):
        self.db = db

    def save_signal(
        self,
        signal: ScoredSignal,
        is_approved: bool,
        rejection_reason: Optional[str] = None,
        regime: Optional[str] = None,
    ) -> None:
        cand = signal.candidate
        sig_id = f"{cand.strategy_id}_{cand.timestamp.strftime('%Y%m%d%H%M%S')}"
        regime_str = regime or "UNKNOWN"
        sql = """
        INSERT OR REPLACE INTO signals (
            signal_id, timestamp, symbol, strategy_id, side, entry_price,
            sl_price, tp_price, confidence_score, regime, is_approved, rejection_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    sql,
                    (
                        sig_id,
                        cand.timestamp.isoformat(),
                        cand.symbol,
                        cand.strategy_id,
                        cand.side.value,
                        cand.entry_price,
                        cand.stop_loss,
                        cand.take_profit,
                        signal.confidence_score,
                        regime_str,
                        1 if is_approved else 0,
                        rejection_reason,
                    ),
                )
        finally:
            conn.close()

    def get_recent_signals(self, limit: int = 50) -> List[dict]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


class EquityRepository:
    def __init__(self, db: Database):
        self.db = db

    def record_snapshot(
        self,
        timestamp: pd.Timestamp,
        balance: float,
        equity: float,
        open_positions: int,
        daily_pnl: float,
    ) -> None:
        sql = """
        INSERT INTO equity_snapshots (timestamp, balance, equity, open_positions_count, daily_pnl)
        VALUES (?, ?, ?, ?, ?)
        """
        conn = self.db.get_connection()
        try:
            with conn:
                conn.execute(
                    sql,
                    (
                        timestamp.isoformat(),
                        balance,
                        equity,
                        open_positions,
                        daily_pnl,
                    ),
                )
        finally:
            conn.close()

    def get_equity_history(self) -> List[dict]:
        conn = self.db.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM equity_snapshots ORDER BY timestamp ASC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
