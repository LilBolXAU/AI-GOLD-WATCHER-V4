"""
Market Session Router for AI GOLD WATCHER V4.
Identifies global trading sessions (Asia, London, New York, Off-Hours)
and routes optimal strategy profiles and trade management parameters dynamically.
"""

from dataclasses import dataclass
from datetime import datetime, time, timezone
from enum import Enum
from typing import List, Optional


class MarketSession(str, Enum):
    ASIAN = "ASIAN"          # Tokyo, Sydney, Hong Kong (Consolidation / Mean Reversion)
    LONDON = "LONDON"        # London / Frankfurt Open (Liquidity Sweeps & Breakouts)
    NEW_YORK = "NEW_YORK"    # Wall Street Open (Peak Volume, Macro Trend Following)
    OFF_HOURS = "OFF_HOURS"  # Asian rollover / Pre-market (Thin liquidity, wide spreads)


@dataclass(frozen=True)
class SessionProfile:
    session: MarketSession
    name_vn: str
    preferred_strategies: List[str]
    allow_trailing_runner: bool
    tp_multiplier: float
    max_allowable_spread_pts: int
    description: str


class SessionRouter:
    """
    Time-of-Day Orchestrator for Gold (XAUUSD).
    Maps current UTC time to market liquidity regimes and strategy preferences.
    """

    # Session Windows in UTC (Gold trades 24/5):
    # Asian Session:    00:00 UTC - 06:30 UTC (07:00 - 13:30 VN)
    # London Session:   07:00 UTC - 11:30 UTC (14:00 - 18:30 VN)
    # New York Session: 12:30 UTC - 17:00 UTC (19:30 - 00:00 VN)
    # Off-Hours:        17:00 UTC - 23:59 UTC (00:00 - 07:00 VN)

    @staticmethod
    def get_current_session(dt: Optional[datetime] = None) -> MarketSession:
        """Determines active market session from UTC datetime."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        t = dt.time()

        # 00:00 <= t < 06:30 -> ASIAN
        if time(0, 0) <= t < time(6, 30):
            return MarketSession.ASIAN

        # 07:00 <= t < 11:30 -> LONDON
        if time(7, 0) <= t < time(11, 30):
            return MarketSession.LONDON

        # 12:30 <= t < 17:00 -> NEW_YORK
        if time(12, 30) <= t < time(17, 0):
            return MarketSession.NEW_YORK

        # Transition zones and late evening -> OFF_HOURS
        return MarketSession.OFF_HOURS

    @classmethod
    def get_profile(cls, dt: Optional[datetime] = None) -> SessionProfile:
        """Returns full trading configuration for the active session."""
        session = cls.get_current_session(dt)

        if session == MarketSession.ASIAN:
            return SessionProfile(
                session=MarketSession.ASIAN,
                name_vn="Phiên Châu Á (Tokyo/Sydney)",
                preferred_strategies=["ASIAN_RANGE_SCALPER", "RANGE_REVERSAL", "SMC_STRUCTURE_PRICE_ACTION", "PULLBACK_CONTINUATION"],
                allow_trailing_runner=False,  # Asia rarely produces 20-point sustained trends
                tp_multiplier=1.0,           # Standard 1:1.5 scalp
                max_allowable_spread_pts=30,
                description="Biên độ hẹp, dòng tiền tích lũy. Thích hợp Scalping đảo chiều đỉnh/đáy ngắn.",
            )

        if session == MarketSession.LONDON:
            return SessionProfile(
                session=MarketSession.LONDON,
                name_vn="Phiên Châu Âu (London)",
                preferred_strategies=["LONDON_LIQUIDITY_SWEEP", "SMC_STRUCTURE_PRICE_ACTION", "VOLATILITY_BREAKOUT", "TREND_FOLLOWING", "PULLBACK_CONTINUATION"],
                allow_trailing_runner=True,  # London breaks out strongly
                tp_multiplier=1.5,           # Extended targets (1:2.0+)
                max_allowable_spread_pts=25,
                description="Thanh khoản tăng mạnh, bẫy quét thanh khoản và sóng bùng nổ mạnh mẽ.",
            )

        if session == MarketSession.NEW_YORK:
            return SessionProfile(
                session=MarketSession.NEW_YORK,
                name_vn="Phiên Mỹ (New York)",
                preferred_strategies=["TREND_FOLLOWING", "SMC_STRUCTURE_PRICE_ACTION", "PULLBACK_CONTINUATION", "VOLATILITY_BREAKOUT", "LONDON_LIQUIDITY_SWEEP"],
                allow_trailing_runner=True,  # NY mega runners
                tp_multiplier=2.0,           # Maximum extension (1:2.5 - 1:3.0)
                max_allowable_spread_pts=25,
                description="Khối lượng giao dịch bùng nổ, có tin tức USD. Sóng mở rộng dài nhất trong ngày.",
            )

        # OFF_HOURS
        return SessionProfile(
            session=MarketSession.OFF_HOURS,
            name_vn="Phiên Đêm / Giờ Giãn Spread",
            preferred_strategies=["PULLBACK_CONTINUATION"],
            allow_trailing_runner=False,
            tp_multiplier=1.0,
            max_allowable_spread_pts=22,  # Strict spread filter during rollover
            description="Thanh khoản mỏng, chênh lệch spread cao. Đề cao phòng thủ và bảo toàn vốn.",
        )

    @classmethod
    def get_strategy_session_bonus(cls, strategy_id: str, dt: Optional[datetime] = None) -> float:
        """
        Calculates confidence score bonus (or penalty) based on session-strategy affinity.
        Range: -5.0 to +5.0 points.
        """
        profile = cls.get_profile(dt)
        if strategy_id in profile.preferred_strategies:
            # First preference gets highest bonus
            rank = profile.preferred_strategies.index(strategy_id)
            return 5.0 if rank == 0 else 3.0
        return -3.0
