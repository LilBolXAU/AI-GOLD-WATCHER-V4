"""
Shared pytest fixtures for AI GOLD WATCHER V4 test suite.
"""

import tempfile
from pathlib import Path
import pytest
import pandas as pd

from src.config.settings import SystemSettings, BrokerSettings, RiskSettings
from src.data.models import SymbolSpec, Timeframe
from src.data.symbol_specs import DEFAULT_EXNESS_XAUUSD
from src.data.mt5_client import MockMT5Client
from src.storage.database import Database
from tests.fixtures.sample_bars import (
    create_trending_bars,
    create_ranging_bars,
    create_shock_bars,
)


@pytest.fixture
def symbol_spec() -> SymbolSpec:
    return DEFAULT_EXNESS_XAUUSD


@pytest.fixture
def default_settings() -> SystemSettings:
    return SystemSettings()


@pytest.fixture
def mock_mt5_client(symbol_spec: SymbolSpec) -> MockMT5Client:
    client = MockMT5Client(spec=symbol_spec)
    client.generate_synthetic_bars(timeframe=Timeframe.M5, count=200, volatility=1.5)
    return client


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test_trading.db"
    return Database(db_file)


@pytest.fixture
def trending_up_df() -> pd.DataFrame:
    return create_trending_bars(direction="up", count=150)


@pytest.fixture
def trending_down_df() -> pd.DataFrame:
    return create_trending_bars(direction="down", count=150)


@pytest.fixture
def ranging_df() -> pd.DataFrame:
    return create_ranging_bars(count=150)


@pytest.fixture
def shock_df() -> pd.DataFrame:
    return create_shock_bars(count=150, shock_index=-1)
