"""
Integration test for full end-to-end execution pipeline.
"""

from datetime import datetime, timezone
import pandas as pd
import pytest

from src.data.models import Timeframe
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.data.mt5_client import MockMT5Client
from src.data.data_engine import MT5DataEngine
from src.indicators.indicator_engine import SharedIndicatorEngine
from src.regime.regime_detector import MarketRegimeDetector
from src.selector.adaptive_selector import AdaptiveStrategySelector
from src.scoring.confidence_engine import ConfidenceEngine
from src.risk.risk_guard import RiskGuard
from src.execution.paper_trade_manager import PaperTradeManager
from src.storage.database import Database
from src.storage.repositories import TradeRepository, SignalRepository, EquityRepository


def test_full_trading_pipeline(temp_db: Database):
    spec = DEFAULT_EXNESS_XAUUSD
    client = MockMT5Client(spec=spec)
    # Generate 150 synthetic bars with volatility
    client.generate_synthetic_bars(timeframe=Timeframe.M5, count=150, volatility=2.0)

    data_engine = MT5DataEngine(client=client, symbol="XAUUSDm")
    assert data_engine.initialize() is True

    # Storage repositories
    trade_repo = TradeRepository(temp_db)
    signal_repo = SignalRepository(temp_db)
    equity_repo = EquityRepository(temp_db)

    # Core engines
    indicator_engine = SharedIndicatorEngine()
    regime_detector = MarketRegimeDetector()
    selector = AdaptiveStrategySelector()
    confidence_engine = ConfidenceEngine(threshold=60.0)
    risk_guard = RiskGuard(spec=spec, reference_balance=50.0)
    paper_mgr = PaperTradeManager(spec=spec, risk_guard=risk_guard)

    bars = client.get_rates("XAUUSDm", Timeframe.M5, count=100, closed_only=True)
    assert len(bars) == 100

    trades_executed = 0
    signals_evaluated = 0

    for i in range(40, len(bars)):
        bar = bars[i]

        # 1. Update active position if present
        closed = paper_mgr.on_bar_update(bar)
        if closed:
            trade_repo.save_closed_trade(closed)

        # 2. Slice historical window up to closed bar
        sub_bars = bars[: i + 1]
        df = pd.DataFrame([
            {"time": b.timestamp, "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.tick_volume, "spread": b.spread}
            for b in sub_bars
        ]).set_index("time")

        # 3. Enrich indicators & detect regime
        enriched = indicator_engine.compute_all(df)
        regime_state = regime_detector.update(enriched)

        # 4. Generate & score signals if no open position
        if paper_mgr.active_position is None:
            cand = selector.evaluate(enriched, regime_state, spec)
            if cand:
                signals_evaluated += 1
                scored = confidence_engine.score(cand, regime_state, bar.spread)
                risk_res = risk_guard.evaluate_signal(scored, bar.spread, bar.timestamp)

                signal_repo.save_signal(
                    signal=scored,
                    is_approved=risk_res.is_approved,
                    rejection_reason=risk_res.rejection_reason,
                    regime=regime_state.regime.value,
                )

                if risk_res.is_approved and risk_res.order:
                    opened = paper_mgr.open_position(risk_res.order, bar.spread, bar.timestamp)
                    if opened:
                        trades_executed += 1

    # Verify records in database
    db_signals = signal_repo.get_recent_signals(limit=100)
    assert len(db_signals) == signals_evaluated

    db_trades = trade_repo.get_all_trades()
    assert len(db_trades) == len(paper_mgr.trade_history)
