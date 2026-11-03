"""
Chronological Event-Driven Backtesting Engine for AI GOLD WATCHER V4.
Strict bar-by-bar evaluation: signal on bar t, fill on bar t+1 open.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd

from src.data.models import BarData, SymbolSpec
from src.indicators.indicator_engine import SharedIndicatorEngine
from src.regime.regime_detector import MarketRegimeDetector, MarketRegimeState, RegimeType
from src.selector.adaptive_selector import AdaptiveStrategySelector
from src.scoring.confidence_engine import ConfidenceEngine
from src.risk.risk_guard import RiskGuard, ApprovedOrder
from src.risk.pnl_calculator import calculate_gross_pnl, calculate_points_pnl
from src.risk.cost_calculator import calculate_spread_cost, calculate_slippage_cost, calculate_net_pnl
from src.execution.virtual_position import VirtualPosition
from src.execution.trade_lifecycle import ClosedTrade, ExitReason
from src.backtest.spread_model import SpreadModel, ConstantSpreadModel
from src.backtest.slippage_model import SlippageModel, FixedSlippageModel
from src.backtest.commission_model import ZeroCommissionModel
from src.backtest.fill_simulator import FillSimulator


@dataclass
class BacktestResult:
    """Complete output of an event-driven backtest run."""
    initial_balance: float
    final_balance: float
    equity_curve: pd.Series
    trades: List[ClosedTrade] = field(default_factory=list)
    regime_history: List[MarketRegimeState] = field(default_factory=list)

    @property
    def total_net_profit(self) -> float:
        return round(self.final_balance - self.initial_balance, 2)

    @property
    def return_pct(self) -> float:
        if self.initial_balance <= 0:
            return 0.0
        return round((self.total_net_profit / self.initial_balance) * 100.0, 2)


class EventBacktestEngine:
    """
    Event-driven backtester faithfully reproducing live execution conditions.
    """

    def __init__(
        self,
        spec: SymbolSpec,
        initial_balance: float = 50.0,
        spread_model: Optional[SpreadModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        warmup_bars: int = 50,
    ):
        self.spec = spec
        self.initial_balance = initial_balance
        self.spread_model = spread_model or ConstantSpreadModel(18)
        self.slippage_model = slippage_model or FixedSlippageModel(1)
        self.warmup_bars = warmup_bars

        # Subsystems
        self.regime_detector = MarketRegimeDetector()
        self.selector = AdaptiveStrategySelector()
        self.confidence_engine = ConfidenceEngine(threshold=65.0)
        self.risk_guard = RiskGuard(spec=spec, reference_balance=initial_balance)
        self.fill_sim = FillSimulator(spec=spec)

    def run(self, df: pd.DataFrame) -> BacktestResult:
        """
        Execute backtest sequentially across the provided OHLCV DataFrame.
        """
        if len(df) < self.warmup_bars + 10:
            raise ValueError(f"Insufficient bars for backtesting (requires > {self.warmup_bars + 10})")

        # 1. Enrich data with indicators upfront (causal rolling formulas)
        enriched_df = SharedIndicatorEngine.compute_all(df)

        equity = self.initial_balance
        cash = self.initial_balance
        equity_series = {}
        trades: List[ClosedTrade] = []
        regimes: List[MarketRegimeState] = []

        active_pos: Optional[VirtualPosition] = None
        pending_order: Optional[ApprovedOrder] = None

        n_bars = len(enriched_df)

        for i in range(self.warmup_bars, n_bars):
            curr_row = enriched_df.iloc[i]
            curr_ts = enriched_df.index[i]
            curr_bar = BarData(
                timestamp=curr_ts,
                open=float(curr_row["open"]),
                high=float(curr_row["high"]),
                low=float(curr_row["low"]),
                close=float(curr_row["close"]),
                tick_volume=int(curr_row.get("volume", 100)),
                spread=int(curr_row.get("spread", 18)),
            )

            # Step 1: Fill any pending order approved on the PREVIOUS bar (bar t-1) at bar t Open
            if pending_order is not None and active_pos is None:
                atr_val = float(curr_row.get("atr_14", 1.0))
                spread_pts = self.spread_model.get_spread_points(i, atr_val)
                slip_pts = self.slippage_model.get_slippage_points(i, atr_val)

                active_pos = self.fill_sim.simulate_entry_fill(
                    order=pending_order,
                    next_bar=curr_bar,
                    spread_pts=spread_pts,
                    slippage_pts=slip_pts,
                )
                self.risk_guard.active_position_count = 1
                pending_order = None

            # Step 2: If a position is active, check if this bar triggered an exit
            if active_pos is not None:
                is_closed, exit_price, exit_reason = self.fill_sim.check_intrabar_exit(active_pos, curr_bar)

                if is_closed and exit_price is not None and exit_reason is not None:
                    # Finalize trade
                    gross_pnl = calculate_gross_pnl(
                        active_pos.entry_price, exit_price, active_pos.side, active_pos.volume, self.spec
                    )
                    pts = calculate_points_pnl(
                        active_pos.entry_price, exit_price, active_pos.side, self.spec
                    )
                    spread_cost = calculate_spread_cost(
                        active_pos.spread_points, active_pos.volume, self.spec
                    )
                    slip_cost = calculate_slippage_cost(
                        active_pos.slippage_points, active_pos.volume, self.spec
                    )
                    net_pnl = calculate_net_pnl(gross_pnl, spread_cost)
                    dur = int((curr_ts - active_pos.entry_time).total_seconds())

                    trade = ClosedTrade(
                        trade_id=f"bt_trd_{len(trades)+1:04d}",
                        magic_number=active_pos.magic_number,
                        strategy_id=active_pos.strategy_id,
                        symbol=active_pos.symbol,
                        side=active_pos.side,
                        volume=active_pos.volume,
                        entry_price=active_pos.entry_price,
                        entry_time=active_pos.entry_time,
                        exit_price=exit_price,
                        exit_time=curr_ts,
                        stop_loss=active_pos.stop_loss,
                        take_profit=active_pos.take_profit,
                        exit_reason=exit_reason,
                        duration_seconds=dur,
                        gross_pnl=gross_pnl,
                        spread_cost=spread_cost,
                        slippage_cost=slip_cost,
                        net_pnl=net_pnl,
                        points_pnl=pts,
                    )
                    trades.append(trade)
                    cash += net_pnl
                    equity = cash
                    self.risk_guard.drawdown_guard.record_trade_result(net_pnl, curr_ts)
                    active_pos = None
                    self.risk_guard.active_position_count = 0
                else:
                    # Update floating equity
                    active_pos.update_price(curr_bar.close, self.spec)
                    equity = cash + active_pos.floating_pnl
            else:
                equity = cash

            equity_series[curr_ts] = round(equity, 2)

            # Step 3: Evaluate new signals on closed bar t (for entry at bar t+1)
            # Only generate signals if we have no active position and no pending order
            if active_pos is None and pending_order is None and i < n_bars - 1:
                sub_df = enriched_df.iloc[: i + 1]
                regime_state = self.regime_detector.update(sub_df)
                regimes.append(regime_state)

                # Skip signal evaluation if regime is unstable
                if regime_state.regime != RegimeType.UNSTABLE:
                    candidate = self.selector.evaluate(sub_df, regime_state, self.spec)
                    if candidate is not None:
                        atr_val = float(curr_row.get("atr_14", 1.0))
                        spread_pts = self.spread_model.get_spread_points(i, atr_val)
                        scored = self.confidence_engine.score(candidate, regime_state, spread_pts)

                        risk_eval = self.risk_guard.evaluate_signal(scored, spread_pts, curr_ts)
                        if risk_eval.is_approved and risk_eval.order is not None:
                            # Order is approved! It will fill at bar t+1 open
                            pending_order = risk_eval.order

        eq_s = pd.Series(equity_series)
        return BacktestResult(
            initial_balance=self.initial_balance,
            final_balance=round(equity, 2),
            equity_curve=eq_s,
            trades=trades,
            regime_history=regimes,
        )
