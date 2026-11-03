"""
Unit tests for Market Session Router (Time-of-Day Orchestrator).
"""

from datetime import datetime, timezone
import pytest

from src.regime.session_router import SessionRouter, MarketSession


def test_asian_session_detection():
    # 03:30 UTC -> Asian Session
    dt = datetime(2026, 11, 3, 3, 30, tzinfo=timezone.utc)
    profile = SessionRouter.get_profile(dt)
    assert profile.session == MarketSession.ASIAN
    assert "RANGE_REVERSAL" in profile.preferred_strategies
    assert profile.allow_trailing_runner is False
    assert profile.max_allowable_spread_pts == 30


def test_london_session_detection():
    # 08:45 UTC -> London Session
    dt = datetime(2026, 11, 3, 8, 45, tzinfo=timezone.utc)
    profile = SessionRouter.get_profile(dt)
    assert profile.session == MarketSession.LONDON
    assert "VOLATILITY_BREAKOUT" in profile.preferred_strategies
    assert profile.allow_trailing_runner is True


def test_new_york_session_detection():
    # 14:15 UTC -> New York Session
    dt = datetime(2026, 11, 3, 14, 15, tzinfo=timezone.utc)
    profile = SessionRouter.get_profile(dt)
    assert profile.session == MarketSession.NEW_YORK
    assert "TREND_FOLLOWING" in profile.preferred_strategies
    assert profile.allow_trailing_runner is True
    assert profile.tp_multiplier == 2.0


def test_off_hours_detection():
    # 22:30 UTC -> Off-Hours / Rollover
    dt = datetime(2026, 11, 3, 22, 30, tzinfo=timezone.utc)
    profile = SessionRouter.get_profile(dt)
    assert profile.session == MarketSession.OFF_HOURS
    assert profile.allow_trailing_runner is False


def test_strategy_session_bonus():
    # London favors Breakout
    dt_london = datetime(2026, 11, 3, 9, 0, tzinfo=timezone.utc)
    bonus_bo = SessionRouter.get_strategy_session_bonus("VOLATILITY_BREAKOUT", dt_london)
    bonus_rr = SessionRouter.get_strategy_session_bonus("RANGE_REVERSAL", dt_london)
    assert bonus_bo > 0
    assert bonus_rr < 0
