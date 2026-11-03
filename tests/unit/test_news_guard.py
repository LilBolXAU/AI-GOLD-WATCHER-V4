"""
Unit tests for High-Impact Economic News Calendar & Blackout Guard.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from src.risk.news_guard import NewsGuard, EconomicNewsEvent
from src.risk.risk_guard import RiskGuard
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.scoring.signal_quality import ScoredSignal
from src.strategies.base_strategy import SignalCandidate, OrderSide


@pytest.fixture
def sample_events():
    t0 = datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 11, 3, 16, 0, tzinfo=timezone.utc)
    return [
        EconomicNewsEvent(
            title="Non-Farm Employment Change",
            country="USD",
            impact="High",
            event_time_utc=t0,
            forecast="150K",
            previous="142K",
        ),
        EconomicNewsEvent(
            title="ISM Manufacturing PMI",
            country="USD",
            impact="High",
            event_time_utc=t1,
            forecast="49.5",
            previous="47.2",
        ),
    ]


@pytest.fixture
def mock_news_guard(sample_events, tmp_path):
    guard = NewsGuard(
        pre_buffer_minutes=15,
        post_buffer_minutes=15,
        alert_advance_minutes=30,
        cache_path=tmp_path / "cache.json",
    )
    guard._events = sample_events
    guard._last_fetch_time = datetime.now(timezone.utc)
    return guard


def test_news_guard_blackout_window(mock_news_guard):
    t_event = datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)

    # 20 minutes before: Safe
    is_bo, ev, _ = mock_news_guard.is_news_blackout(t_event - timedelta(minutes=20))
    assert not is_bo

    # 10 minutes before (in pre-buffer): Blackout
    is_bo, ev, reason = mock_news_guard.is_news_blackout(t_event - timedelta(minutes=10))
    assert is_bo
    assert ev.title == "Non-Farm Employment Change"
    assert "blackout active" in reason

    # Exact event time: Blackout
    is_bo, ev, _ = mock_news_guard.is_news_blackout(t_event)
    assert is_bo

    # 10 minutes after (in post-buffer): Blackout
    is_bo, ev, _ = mock_news_guard.is_news_blackout(t_event + timedelta(minutes=10))
    assert is_bo

    # 20 minutes after: Safe
    is_bo, ev, _ = mock_news_guard.is_news_blackout(t_event + timedelta(minutes=20))
    assert not is_bo


def test_news_guard_upcoming_alert_dedup(mock_news_guard):
    t_event = datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)

    # 40 minutes before: too early for 30m alert
    res = mock_news_guard.check_upcoming_alert(t_event - timedelta(minutes=40))
    assert res is None

    # 25 minutes before: should trigger alert
    res = mock_news_guard.check_upcoming_alert(t_event - timedelta(minutes=25))
    assert res is not None
    ev, mins = res
    assert ev.title == "Non-Farm Employment Change"
    assert mins == 25

    # Second check at 24 minutes before: should not re-trigger (prevent spam)
    res2 = mock_news_guard.check_upcoming_alert(t_event - timedelta(minutes=24))
    assert res2 is None


def test_news_guard_get_next_event(mock_news_guard):
    cur_time = datetime(2026, 11, 3, 13, 30, tzinfo=timezone.utc)
    next_ev = mock_news_guard.get_next_event(cur_time)
    assert next_ev is not None
    ev, mins = next_ev
    assert ev.title == "Non-Farm Employment Change"
    assert mins == 60


def test_risk_guard_news_blackout_veto(mock_news_guard):
    risk_guard = RiskGuard(
        spec=DEFAULT_EXNESS_XAUUSD,
        news_guard=mock_news_guard,
        reference_balance=50.0,
        max_sl_pts=350,
    )

    t_event = datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc)
    cand = SignalCandidate(
        strategy_id="trend_following",
        symbol="XAUUSDm",
        side=OrderSide.BUY,
        entry_price=3900.0,
        stop_loss=3898.5,
        take_profit=3903.0,
        raw_confidence=80.0,
        timestamp=t_event - timedelta(minutes=5),  # 5 min before news -> blackout!
    )
    scored = ScoredSignal(
        candidate=cand,
        total_score=80.0,
        passes_threshold=True,
    )

    res = risk_guard.evaluate_signal(
        scored=scored,
        current_spread=20,
        current_time=cand.timestamp,
    )

    assert not res.is_approved
    assert "High-impact news blackout active" in res.rejection_reason
